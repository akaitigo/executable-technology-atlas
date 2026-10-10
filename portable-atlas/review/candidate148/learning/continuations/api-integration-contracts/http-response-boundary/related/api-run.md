{
  "command": "python3 -B experiment.py",
  "finished_at": "2026-10-05T06:24:27+00:00",
  "input": {
    "body_budget_bytes": 8192,
    "cases": [
      {
        "body": "{\"id\":7,\"name\":\"sample\"}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "base",
        "status": 200,
        "title": "既存契約：idとname"
      },
      {
        "body": "{\"id\":7,\"name\":\"sample\",\"note\":\"v2\",\"extra\":true}",
        "content_type": "application/json; charset=utf-8",
        "delay_seconds": 0,
        "id": "optional",
        "status": 200,
        "title": "optional field追加：互換を維持"
      },
      {
        "body": "{\"id\":7}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "missing",
        "status": 200,
        "title": "必須name欠落：拒否"
      },
      {
        "body": "{\"id\":\"7\",\"name\":\"sample\"}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "type-changed",
        "status": 200,
        "title": "idがstringへ変更：拒否"
      },
      {
        "body": "{\"id\":true,\"name\":\"sample\"}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "boolean-id",
        "status": 200,
        "title": "booleanをinteger扱いしない"
      },
      {
        "body": "{\"id\":7,\"name\":\"sample\"}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "status-changed",
        "status": 201,
        "title": "201：HTTP成功でもこの契約は拒否"
      },
      {
        "body": "{\"id\":7,\"name\":\"sample\"}",
        "content_type": "text/plain",
        "delay_seconds": 0,
        "id": "media-changed",
        "status": 200,
        "title": "text/plain：JSON文字列でも拒否"
      },
      {
        "body": "{\"id\":7,",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "malformed",
        "status": 200,
        "title": "壊れたJSON：拒否"
      },
      {
        "body": "",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "empty-body",
        "status": 200,
        "title": "200だがbody空：拒否"
      },
      {
        "body": "{\"error\":{\"code\":\"invalid_input\",\"message\":\"synthetic rejection\"}}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "api-error",
        "status": 422,
        "title": "422とerror body：エラーとして処理"
      },
      {
        "body": "{\"id\":7,\"name\":\"sample\"}",
        "content_type": "application/json",
        "delay_seconds": 0,
        "id": "bad-error",
        "status": 422,
        "title": "422だがerror body契約欠落"
      },
      {
        "body": "{\"id\":7,\"name\":\"late\"}",
        "content_type": "application/json",
        "delay_seconds": 0.6,
        "id": "timeout",
        "status": 200,
        "title": "応答前delay：socket timeoutで停止"
      }
    ],
    "contract": {
      "error_schema": {
        "properties": {
          "error": {
            "properties": {
              "code": {
                "minLength": 1,
                "type": "string"
              },
              "message": {
                "minLength": 1,
                "type": "string"
              }
            },
            "required": [
              "code",
              "message"
            ],
            "type": "object"
          }
        },
        "required": [
          "error"
        ],
        "type": "object"
      },
      "error_status": 422,
      "id": "synthetic-item-v1",
      "implementation_boundary": "Handwritten checks implement only these fixed rules, not a general JSON Schema evaluator. 200/422, optional note and extra field tolerance are this API contract, not universal HTTP rules.",
      "media_type": "application/json",
      "success_schema": {
        "additionalProperties": true,
        "properties": {
          "id": {
            "minimum": 1,
            "type": "integer"
          },
          "name": {
            "minLength": 1,
            "type": "string"
          },
          "note": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "name"
        ],
        "type": "object"
      },
      "success_status": 200
    },
    "request_schedule": "12 sequential GETs; no automatic retry",
    "timeout_design": "socket timeout 0.1s for delayed case; 2s otherwise; outer observation subprocess budget 15s"
  },
  "process": {
    "attempts": 1,
    "exit_code": 0,
    "retries": 0,
    "timeout_seconds": 15
  },
  "publication": "full-run-passed; directory rename with rollback; retain prior success",
  "runtime": {
    "architecture": "arm64",
    "client": "stdlib http.client.HTTPConnection",
    "http_version": "HTTP/1.1",
    "os": "Darwin",
    "python_version": "3.9.6",
    "server": "stdlib http.server.HTTPServer"
  },
  "source_digests": {
    "COVERAGE.md": "sha256:eba55203822483e5ab44c272ea71bdfd00ec12790c5722da1f981b968399ff2f",
    "README.md": "sha256:0064c23805f909efff1a5b59607f5ee4c2af82040e5732e2112494df99ea21af",
    "app.js": "sha256:1330b4fe0d42a8a738bab740c08e860ed6e0f3dc06e0959600c8cebb16e4bf69",
    "cases.json": "sha256:5a6e1cd146a2d055dbe3768289cca5a608e11f96eb275fb6e39912984c18e97e",
    "client.py": "sha256:2e890e4c1d6269df041df1096cacbf6e91bcc37143dac06f5273b9805a394c8a",
    "contract.json": "sha256:53b7f74c6d1a48506bd1d6267f191c34e4792ceec9936340618d5f153fbe02d1",
    "experiment.py": "sha256:02eb04bd3277d9528906fdf5037f3a13c0748c54ca740e48989084c307c461dc",
    "index.html": "sha256:595b42829072f39fbd1eb0fd074d4cb25e4306765db73b7e5a8e71a7feb84bdb",
    "observe.py": "sha256:78007bb47a2f38c08dffd9ec7d1b205a8bc1028df3d8cb6205f7b69bd323fdc7",
    "skills/atlas-api-integration-contracts/SKILL.md": "sha256:37fd27f0f9c3066197e494cedb675e3c6c272b319063456a5893136db622e078",
    "sources.json": "sha256:84a7d3d296bc8fec0469bb1b14c36fd7b64daf858c58fd13071de5ed8340f741",
    "style.css": "sha256:dacc260c8ef615297cfbbd44f47296502f1f1042904d4cde1c944e48fa2d2c79",
    "test_contract.py": "sha256:a72c8e778946828f2b65e71f32f637c2e71fdc6b71d0462a4773ef067d4658b5",
    "verify.py": "sha256:e2bee7ef1d273d329a6c8e572deb117acee2ae07ce9609366488ed1fdcaecdcc"
  },
  "started_at": "2026-10-05T06:24:26+00:00",
  "status": "passed-with-demonstrated-rejections",
  "stdout_digest": "sha256:220ce29d32afa59ea8d02db20298a4c2fda3405d8287e2aa6b960f675c165f0d",
  "subject": "api-integration-contracts"
}
