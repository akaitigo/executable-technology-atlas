{
  "subject":"api-integration-contracts","checked_on":"2026-10-05","third_party_body_saved":false,
  "sources":[
    {"id":"http-semantics","title":"RFC 9110 HTTP Semantics","publisher":"IETF / RFC Editor","url":"https://www.rfc-editor.org/rfc/rfc9110.html","locators":["8.3 Content-Type","15.3.1 200 OK","15.3.2 201 Created","15.5.21 422 Unprocessable Content","9.2.2 Idempotent Methods","8.8 Validators"],"supports":"HTTP status/media semantics and future idempotency/cache experiments, not this API's schema rules"},
    {"id":"json","title":"RFC 8259 JSON","publisher":"IETF / RFC Editor","url":"https://www.rfc-editor.org/rfc/rfc8259.html","locators":["3 Values","4 Objects","6 Numbers","8.1 Character Encoding"],"supports":"JSON syntax and distinct number/string/boolean types; lesson does not certify full parser conformance"},
    {"id":"python-server","title":"Python 3.9 http.server","publisher":"Python documentation","url":"https://docs.python.org/3.9/library/http.server.html","locators":["HTTPServer","BaseHTTPRequestHandler","not recommended for production"],"supports":"actual stdlib loopback server implementation and production boundary"},
    {"id":"python-client","title":"Python 3.9 http.client","publisher":"Python documentation","url":"https://docs.python.org/3.9/library/http.client.html","locators":["HTTPConnection timeout","request","getresponse","HTTPResponse.read"],"supports":"actual client and socket timeout; not a general end-to-end deadline"},
    {"id":"problem-details","title":"RFC 9457 Problem Details for HTTP APIs","publisher":"IETF / RFC Editor","url":"https://www.rfc-editor.org/rfc/rfc9457.html","locators":["3 The Problem Details JSON Object"],"supports":"future error representation experiment; current custom error body is not RFC 9457 implementation"}
  ],
  "design_boundary":"200 success, 422 custom error, optional/extra field policy, fixed handwritten schema checks and case oracle are lesson choices. Only own loopback HTTP/1.1 is executed. No third-party prose/images saved."
}
