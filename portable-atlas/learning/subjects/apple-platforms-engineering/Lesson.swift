import Foundation

struct Profile: Codable {
    let name: String
    let age: Int8
    let note: String?
    enum CodingKeys: String, CodingKey { case name, age, note }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = try c.decode(String.self, forKey: .name)
        age = try c.decode(Int8.self, forKey: .age)
        note = try c.decodeIfPresent(String.self, forKey: .note)
    }
}
struct EagerOptional: Decodable {
    let name: String
    let age: Int8
    let note: String
    enum CodingKeys: String, CodingKey { case name, age, note }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = try c.decode(String.self, forKey: .name)
        age = try c.decode(Int8.self, forKey: .age)
        note = try c.decode(String.self, forKey: .note) // deliberate error: optional required
    }
}
struct Defaulting: Decodable {
    let name: String
    let age: Int8
    let note: String?
    enum CodingKeys: String, CodingKey { case name, age, note }
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = (try? c.decode(String.self, forKey: .name)) ?? ""
        age = (try? c.decode(Int8.self, forKey: .age)) ?? 0
        note = try? c.decode(String.self, forKey: .note) // deliberate error: masks wrong type
    }
}
struct Input: Decodable { let id: String; let json: String }
func profile(_ name: String, _ age: Int8, _ note: String?) -> [String: Any] {
    ["name":name, "age":Int(age), "note":note.map { $0 as Any } ?? NSNull()]
}
func path(_ context: DecodingError.Context) -> [String] { context.codingPath.map { $0.stringValue } }
func failure(_ error: Error) -> [String: Any] {
    var kind = "other", keys: [String] = [], debug = String(describing:error)
    switch error {
    case DecodingError.keyNotFound(let key, let c): kind = "keyNotFound"; keys = path(c)+[key.stringValue]; debug = c.debugDescription
    case DecodingError.valueNotFound(_, let c): kind = "valueNotFound"; keys = path(c); debug = c.debugDescription
    case DecodingError.typeMismatch(_, let c): kind = "typeMismatch"; keys = path(c); debug = c.debugDescription
    case DecodingError.dataCorrupted(let c): kind = "dataCorrupted"; keys = path(c); debug = c.debugDescription
    default: break
    }
    return ["status":"rejected", "profile":NSNull(), "error":["kind":kind,"coding_path":keys,"debug":debug]]
}
func decode(_ text: String, variant: String) -> [String: Any] {
    do {
        let data = Data(text.utf8), decoder = JSONDecoder()
        var p: [String: Any]
        switch variant {
        case "normal": let v = try decoder.decode(Profile.self,from:data); p = profile(v.name,v.age,v.note)
        case "eager-optional": let v = try decoder.decode(EagerOptional.self,from:data); p = profile(v.name,v.age,v.note)
        default: let v = try decoder.decode(Defaulting.self,from:data); p = profile(v.name,v.age,v.note)
        }
        return ["status":"accepted", "profile":p,"error":NSNull()]
    } catch { return failure(error) }
}
do {
    let input = FileHandle.standardInput.readDataToEndOfFile()
    let cases = try JSONDecoder().decode([Input].self,from:input)
    var rows: [[String:Any]] = []
    for c in cases {
        var variants: [String:Any] = [:]
        for v in ["normal","eager-optional","defaulting"] { variants[v] = decode(c.json,variant:v) }
        rows.append(["id":c.id,"json":c.json,"variants":variants])
    }
    let output = try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys])
    FileHandle.standardOutput.write(output)
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    FileHandle.standardError.write(Data("invalid harness input\n".utf8))
    exit(2)
}
