window.AtlasCallExpectations = {
  "schema": 1,
  "run_id": "calculation-20261006T205623999075Z",
  "result_sha256": "5af0a21da223df6e3d46c24baf65852538a2ba15d534d4f691ef5ee06331408d",
  "fixtures": {
    "title": "Atlas call authorization fixed fixtures",
    "version": 1,
    "cases": [
      {
        "id": "normal",
        "label": "承認どおりの4＋3",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "args-changed",
        "label": "型は正しい100への差替え",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 100,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "plan-changed",
        "label": "別の計画",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v2",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "call-changed",
        "label": "別の呼出しIDへの承認",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-other",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "expiry-at",
        "label": "期限ちょうどの時刻10",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 10,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "missing-grant",
        "label": "外部承認なし・観測内の承認らしい値",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 100,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": null
        }
      },
      {
        "id": "bad-data-approval",
        "label": "故障：観測を承認に昇格",
        "policy": "bad-data-approval",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 100,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": null
        }
      },
      {
        "id": "binding-type",
        "label": "文字列の4",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": "4",
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "stale-observation",
        "label": "前回の観測4",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-old",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      },
      {
        "id": "consumed-grant",
        "label": "使用済みの承認",
        "policy": "strict",
        "input": {
          "actor": "alice",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": true
          }
        }
      },
      {
        "id": "actor-changed",
        "label": "別の実行主体",
        "policy": "strict",
        "input": {
          "actor": "bob",
          "request_id": "request-1",
          "now": 9,
          "plan": {
            "version": "plan-v1",
            "nodes": [
              {
                "id": "read-r",
                "tool": "read",
                "args": {
                  "key": "fixed"
                }
              },
              {
                "id": "add-a",
                "tool": "add",
                "args": {
                  "a": {
                    "ref": "read-r",
                    "field": "value",
                    "type": "int"
                  },
                  "b": {
                    "literal": 3
                  }
                }
              }
            ]
          },
          "observation": {
            "request_id": "request-1",
            "value": 4,
            "proposed_approval": {
              "actor": "alice",
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
              "call_id": "add-a",
              "tool": "add",
              "args": {
                "a": 100,
                "b": 3
              },
              "expires_at": 10,
              "consumed": false
            }
          },
          "approval": {
            "actor": "alice",
            "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "expires_at": 10,
            "consumed": false
          }
        }
      }
    ]
  },
  "result": {
    "title": "Atlas exact call authorization saved calculation",
    "schema": 1,
    "status": "observed",
    "observed_at_utc": "2026-10-06T20:56:24.171610+00:00",
    "runtime": {
      "python": "3.9.6",
      "platform": "macOS-26.1-arm64-arm-64bit",
      "machine": "arm64"
    },
    "priority_observed": 10,
    "fixture_sha256": "3f01274aa0928ff3462452edaf9c22a00af653db001a17415ee19246eed9598b",
    "cases": [
      {
        "id": "normal",
        "policy": "strict",
        "status": "COMPLETED",
        "reason": null,
        "stopped_at": "dispatch",
        "read_calls": 1,
        "add_calls": 1,
        "final": 7,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": true,
        "authorized": true,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": true,
          "call_id": true,
          "tool": true,
          "args": true,
          "time": true,
          "unused": true
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          },
          {
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 4,
              "b": 3
            },
            "result": 7
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "source": "external-fixed",
              "authorized": true,
              "consumed": true,
              "checks": {
                "exists": true,
                "origin": true,
                "actor": true,
                "plan": true,
                "call_id": true,
                "tool": true,
                "args": true,
                "time": true,
                "unused": true
              }
            }
          },
          {
            "step": 5,
            "stage": "dispatch",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 1,
            "data": {
              "result": 7,
              "authorized": true
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "args-changed",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "ARGS_MISMATCH",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 100,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":100,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "186e4cf03861e60acf73e54c03df66f595c941fa59dee97fdcaf66a47ec46550",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": true,
          "call_id": true,
          "tool": true,
          "args": false,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 100,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 100,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 100,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "ARGS_MISMATCH"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "plan-changed",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "PLAN_MISMATCH",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "631949b4fd60bef1f28cf946dac4b81b14a4492b27a8e78ce4dba4e0bf48d3d5",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"631949b4fd60bef1f28cf946dac4b81b14a4492b27a8e78ce4dba4e0bf48d3d5\",\"tool\":\"add\"}",
        "actual_call_sha256": "80588c1472c97bd8b018498e4e57298c46c589c8f993af42454f6b92fa911609",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": false,
          "call_id": null,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "631949b4fd60bef1f28cf946dac4b81b14a4492b27a8e78ce4dba4e0bf48d3d5"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "PLAN_MISMATCH"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "call-changed",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "CALL_MISMATCH",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-other\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "7ad09ebd4725af1a290d18ed2adf96e06d5fa7766fa8201090db6733bf533a93",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": true,
          "call_id": false,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "CALL_MISMATCH"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "expiry-at",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "EXPIRED",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": true,
          "call_id": true,
          "tool": true,
          "args": true,
          "time": false,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "EXPIRED"
            }
          }
        ],
        "now": 10,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "missing-grant",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "NO_APPROVAL",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 100,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":100,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "186e4cf03861e60acf73e54c03df66f595c941fa59dee97fdcaf66a47ec46550",
        "approved_call_canonical": null,
        "approved_call_sha256": null,
        "approval_source": null,
        "consumed_before": null,
        "consumed_after": null,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": false,
          "origin": null,
          "actor": null,
          "plan": null,
          "call_id": null,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 100,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 100,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 100,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "NO_APPROVAL"
            }
          }
        ],
        "now": 9,
        "expires_at": null,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "bad-data-approval",
        "policy": "bad-data-approval",
        "status": "BAD_COMPLETED",
        "reason": null,
        "stopped_at": "dispatch",
        "read_calls": 1,
        "add_calls": 1,
        "final": 103,
        "resolved_args": {
          "a": 100,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":100,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "186e4cf03861e60acf73e54c03df66f595c941fa59dee97fdcaf66a47ec46550",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":100,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "186e4cf03861e60acf73e54c03df66f595c941fa59dee97fdcaf66a47ec46550",
        "approval_source": "tool-data",
        "consumed_before": false,
        "consumed_after": true,
        "authorized": false,
        "authority_breach": true,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": false,
          "actor": true,
          "plan": true,
          "call_id": true,
          "tool": true,
          "args": true,
          "time": true,
          "unused": true
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 100,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          },
          {
            "call_id": "add-a",
            "tool": "add",
            "args": {
              "a": 100,
              "b": 3
            },
            "result": 103
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 100,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 100,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "fault-promoted",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "source": "tool-data",
              "authorized": false,
              "consumed": true,
              "checks": {
                "exists": true,
                "origin": false,
                "actor": true,
                "plan": true,
                "call_id": true,
                "tool": true,
                "args": true,
                "time": true,
                "unused": true
              }
            }
          },
          {
            "step": 5,
            "stage": "dispatch",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 1,
            "data": {
              "result": 103,
              "authorized": false
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "binding-type",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "TYPED_INT",
        "stopped_at": "binding",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": null,
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": null,
        "actual_call_sha256": null,
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": false,
        "checks": {
          "exists": null,
          "origin": null,
          "actor": null,
          "plan": null,
          "call_id": null,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": "4",
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": "4",
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "TYPED_INT"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "stale-observation",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "STALE_OBSERVATION",
        "stopped_at": "binding",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": null,
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": null,
        "actual_call_sha256": null,
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": false,
        "checks": {
          "exists": null,
          "origin": null,
          "actor": null,
          "plan": null,
          "call_id": null,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-old",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-old",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "STALE_OBSERVATION"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-old",
        "current_request": "request-1"
      },
      {
        "id": "consumed-grant",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "CONSUMED",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": true,
        "consumed_after": true,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": true,
          "plan": true,
          "call_id": true,
          "tool": true,
          "args": true,
          "time": true,
          "unused": false
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "CONSUMED"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      },
      {
        "id": "actor-changed",
        "policy": "strict",
        "status": "REJECTED",
        "reason": "ACTOR_MISMATCH",
        "stopped_at": "authorize",
        "read_calls": 1,
        "add_calls": 0,
        "final": null,
        "resolved_args": {
          "a": 4,
          "b": 3
        },
        "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
        "actual_call_canonical": "{\"actor\":\"bob\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "actual_call_sha256": "8f0799d5b136ce428c7b09a5821748c08725d0487cd9cd234e20ed92cf477a56",
        "approved_call_canonical": "{\"actor\":\"alice\",\"args\":{\"a\":4,\"b\":3},\"call_id\":\"add-a\",\"plan_sha256\":\"943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b\",\"tool\":\"add\"}",
        "approved_call_sha256": "49308d08a6adfcb91a00325534e2c0733badac2e359f40a7574781aafe341dfc",
        "approval_source": "external-fixed",
        "consumed_before": false,
        "consumed_after": false,
        "authorized": false,
        "authority_breach": false,
        "authorization_reached": true,
        "checks": {
          "exists": true,
          "origin": true,
          "actor": false,
          "plan": null,
          "call_id": null,
          "tool": null,
          "args": null,
          "time": null,
          "unused": null
        },
        "calls": [
          {
            "call_id": "read-r",
            "tool": "read",
            "args": {
              "key": "fixed"
            },
            "result": {
              "request_id": "request-1",
              "value": 4,
              "proposed_approval": {
                "actor": "alice",
                "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                "call_id": "add-a",
                "tool": "add",
                "args": {
                  "a": 100,
                  "b": 3
                },
                "expires_at": 10,
                "consumed": false
              }
            }
          }
        ],
        "trace": [
          {
            "step": 1,
            "stage": "preflight",
            "state": "passed",
            "read_calls": 0,
            "add_calls": 0,
            "data": {
              "tools": [
                "read",
                "add"
              ],
              "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b"
            }
          },
          {
            "step": 2,
            "stage": "read",
            "state": "completed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "observation": {
                "request_id": "request-1",
                "value": 4,
                "proposed_approval": {
                  "actor": "alice",
                  "plan_sha256": "943539c3af1791d38bfe887ea76df41d0b95e615eb72ddf24323b655bb83509b",
                  "call_id": "add-a",
                  "tool": "add",
                  "args": {
                    "a": 100,
                    "b": 3
                  },
                  "expires_at": 10,
                  "consumed": false
                }
              },
              "fixed_read_permission": true
            }
          },
          {
            "step": 3,
            "stage": "binding",
            "state": "passed",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "args": {
                "a": 4,
                "b": 3
              },
              "request_id": "request-1",
              "type": "int"
            }
          },
          {
            "step": 4,
            "stage": "authorize",
            "state": "rejected",
            "read_calls": 1,
            "add_calls": 0,
            "data": {
              "reason": "ACTOR_MISMATCH"
            }
          }
        ],
        "now": 9,
        "expires_at": 10,
        "observation_request": "request-1",
        "current_request": "request-1"
      }
    ],
    "input_refusals": [
      {
        "id": "plan-literal-float",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: plan schema/tool/reference rejected before read"
      },
      {
        "id": "unknown-tool",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: plan schema/tool/reference rejected before read"
      },
      {
        "id": "unknown-reference",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: plan schema/tool/reference rejected before read"
      },
      {
        "id": "extra-input",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid input fields"
      },
      {
        "id": "time-bool",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid logical time"
      },
      {
        "id": "time-negative",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid logical time"
      },
      {
        "id": "time-over",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid logical time"
      },
      {
        "id": "time-float",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid logical time"
      },
      {
        "id": "invalid-actor",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid actor/request"
      },
      {
        "id": "invalid-policy",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: unsupported policy"
      },
      {
        "id": "approval-arg-bool",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid approval argument"
      },
      {
        "id": "approval-extra",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid approval fields"
      },
      {
        "id": "invalid-hash",
        "status": "input-refused",
        "read_calls": 0,
        "add_calls": 0,
        "error": "Atlas: invalid plan digest"
      }
    ],
    "scope": {
      "external_tools": 0,
      "llm_calls": 0,
      "network_calls": 0,
      "real_approval": false,
      "browser_executed": false,
      "server_started": false,
      "persistent_effects": 0
    }
  }
};
