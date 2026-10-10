import Foundation
struct Measure: Codable {
 let character: Int, scalar: Int, utf16: Int, utf8: Int
 let codepoints: [UInt32]
 let utf8_hex: String
 init(_ value: String) {
  character = value.count; scalar = value.unicodeScalars.count
  utf16 = value.utf16.count; utf8 = value.utf8.count
  codepoints = value.unicodeScalars.map { $0.value }
  utf8_hex = value.utf8.map { String(format: "%02x", $0) }.joined()
 }
}
struct Decision: Codable { let scalar_ok: Bool, byte_ok: Bool, accepted: Bool }
struct Result: Codable {
 let status: String
 let exception_class: String?
 let decoded: Measure?, redecoded: Measure?
 let normal: Decision?, faulty: Decision?
 let scalar_sequence_preserved: Bool?, utf8_preserved: Bool?
 let encoded_json: String?
 // Emit explicit nulls so input refusal cannot retain an old successful measurement.
 func encode(to encoder: Encoder) throws {
  var c = encoder.container(keyedBy: CodingKeys.self)
  try c.encode(status, forKey: .status); try c.encode(exception_class, forKey: .exception_class)
  try c.encode(decoded, forKey: .decoded);try c.encode(redecoded, forKey: .redecoded)
  try c.encode(normal, forKey: .normal);try c.encode(faulty, forKey: .faulty)
  try c.encode(scalar_sequence_preserved, forKey: .scalar_sequence_preserved);try c.encode(utf8_preserved, forKey: .utf8_preserved);try c.encode(encoded_json, forKey: .encoded_json)
 }
 enum CodingKeys: String, CodingKey {case status,exception_class,decoded,redecoded,normal,faulty,scalar_sequence_preserved,utf8_preserved,encoded_json}
}
let input = FileHandle.standardInput.readDataToEndOfFile()
let result: Result
var code: Int32 = 0
let text: String?
var decodeError: Error?
do { text = try JSONDecoder().decode(String.self, from: input) } catch { text = nil; decodeError = error }
if let text = text {
 do {
  let wire = try JSONEncoder().encode(text)
  let back = try JSONDecoder().decode(String.self, from: wire)
  let first = Measure(text), second = Measure(back)
  let scalarOK = (1...4).contains(first.scalar), byteOK = (1...8).contains(first.utf8)
  let wrongScalarOK = (1...4).contains(first.character)
  result = Result(status:"observed",exception_class:nil,decoded:first,redecoded:second,normal:Decision(scalar_ok:scalarOK,byte_ok:byteOK,accepted:scalarOK && byteOK),faulty:Decision(scalar_ok:wrongScalarOK,byte_ok:byteOK,accepted:wrongScalarOK && byteOK),scalar_sequence_preserved:first.codepoints == second.codepoints,utf8_preserved:first.utf8_hex == second.utf8_hex,encoded_json:String(data:wire,encoding:.utf8))
 } catch {
  result = Result(status:"execution_error",exception_class:String(describing:type(of:error)),decoded:nil,redecoded:nil,normal:nil,faulty:nil,scalar_sequence_preserved:nil,utf8_preserved:nil,encoded_json:nil);code=3
 }
} else {
 result = Result(status:"input_refusal",exception_class:String(describing:type(of:decodeError!)),decoded:nil,redecoded:nil,normal:nil,faulty:nil,scalar_sequence_preserved:nil,utf8_preserved:nil,encoded_json:nil);code=2
}
let encoder = JSONEncoder();encoder.outputFormatting = [.sortedKeys]
do { let output = try encoder.encode(result);FileHandle.standardOutput.write(output);FileHandle.standardOutput.write(Data([10])) } catch { FileHandle.standardError.write(Data("result encoding error\n".utf8));code=3 }
exit(code)
