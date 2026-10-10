import Foundation

let modeKey = CodingUserInfoKey(rawValue: "lesson-mode")!
struct VersionedProfile: Codable {
    let inputVersion: Int
    let name: String
    let displayName: String?
    let inputPresence: String
    enum RootKeys: String, CodingKey { case version, profile }
    enum ProfileKeys: String, CodingKey { case name, displayName }
    init(from decoder: Decoder) throws {
        let root = try decoder.container(keyedBy: RootKeys.self)
        inputVersion = try root.decode(Int.self, forKey: .version)
        guard inputVersion == 1 || inputVersion == 2 else {
            throw DecodingError.dataCorruptedError(forKey: .version, in: root, debugDescription: "UNKNOWN_VERSION")
        }
        let profile = try root.nestedContainer(keyedBy: ProfileKeys.self, forKey: .profile)
        name = try profile.decode(String.self, forKey: .name)
        if !profile.contains(.displayName) { inputPresence = "missing" }
        else if try profile.decodeNil(forKey: .displayName) { inputPresence = "null" }
        else { inputPresence = "value" }
        if decoder.userInfo[modeKey] as? String == "fallback" {
            // Intentional faulty contrast: collapses missing and explicit null.
            displayName = try profile.decodeIfPresent(String.self, forKey: .displayName) ?? name
        } else if inputPresence == "missing" {
            guard inputVersion == 1 else {
                throw DecodingError.keyNotFound(ProfileKeys.displayName, .init(codingPath: profile.codingPath, debugDescription: "V2_REQUIRED_DISPLAY_NAME_KEY"))
            }
            displayName = name
        } else if inputPresence == "null" { displayName = nil }
        else { displayName = try profile.decode(String.self, forKey: .displayName) }
    }
    func encode(to encoder: Encoder) throws {
        var root = encoder.container(keyedBy: RootKeys.self)
        try root.encode(2, forKey: .version)
        var profile = root.nestedContainer(keyedBy: ProfileKeys.self, forKey: .profile)
        try profile.encode(name, forKey: .name)
        if let value = displayName { try profile.encode(value, forKey: .displayName) }
        else { try profile.encodeNil(forKey: .displayName) }
    }
    var profileValue: [String: Any] { ["name": name, "displayName": displayName as Any? ?? NSNull()] }
}
struct Request: Decodable { let `case`: String; let mode: String; let json: String }
func classify(_ error: Error) -> [String: Any] {
    switch error {
    case DecodingError.keyNotFound(let key, let context):return ["kind":"keyNotFound", "key":key.stringValue,"path":context.codingPath.map(\.stringValue),"message":context.debugDescription]
    case DecodingError.typeMismatch(_, let context):return ["kind":"typeMismatch", "key":NSNull(),"path":context.codingPath.map(\.stringValue),"message":context.debugDescription]
    case DecodingError.valueNotFound(_, let context):return ["kind":"valueNotFound", "key":NSNull(),"path":context.codingPath.map(\.stringValue),"message":context.debugDescription]
    case DecodingError.dataCorrupted(let context):return ["kind":"dataCorrupted", "key":"version","path":context.codingPath.map(\.stringValue),"message":context.debugDescription]
    default:return ["kind":String(describing:type(of:error)),"key":NSNull(),"path":[],"message":String(describing:error)]
    }
}
func execute(_ request: Request) -> [String: Any] {
    var phase = "decode"
    do {
        let decoder = JSONDecoder();decoder.userInfo[modeKey] = request.mode
        let original = try decoder.decode(VersionedProfile.self, from: Data(request.json.utf8))
        phase = "encode"
        let encoded = try JSONEncoder().encode(original)
        let encodedText = String(data: encoded, encoding: .utf8)!
        phase = "redecode"
        // Strict v2 redecoder does not use faulty input mode.
        let again = try JSONDecoder().decode(VersionedProfile.self, from: encoded)
        var failed = false
        if request.mode == "fallback" {
            failed = (original.inputPresence == "null" || (original.inputVersion == 2 && original.inputPresence == "missing"))
        }
        return ["case": request.case, "status": request.mode == "fallback" ? (failed ? "BAD_ACCEPTED" : "FAULT_CONTROL") : "ROUNDTRIPPED", "decode_accepted":true,"input_version":original.inputVersion,"input_presence":original.inputPresence,"migrated":original.profileValue,"encoded_text":encodedText,"roundtrip":again.profileValue,"roundtrip_version":again.inputVersion,"roundtrip_presence":again.inputPresence,"rule_failed":failed]
    } catch {
        let expected = phase == "decode" && error is DecodingError
        return ["case":request.case,"status":expected ? "INPUT_REJECTED" : "EXECUTION_FAILURE","phase":phase,"decode_accepted":false,"error":classify(error),"encoded_text":NSNull(),"migrated":NSNull(),"roundtrip":NSNull()]
    }
}
do {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    let requests = try JSONDecoder().decode([Request].self, from:data)
    let results = requests.map(execute)
    let output = try JSONSerialization.data(withJSONObject:results,options:[])
    FileHandle.standardOutput.write(output);FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    let message = "REQUEST_PROCESS_FAILURE: \(error)\n"
    FileHandle.standardError.write(Data(message.utf8));exit(2)
}
