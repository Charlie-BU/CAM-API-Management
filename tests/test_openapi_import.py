import unittest

from services.openapi_import import OpenApiImportError, parseOpenApiDocument


class OpenApiImportParserTest(unittest.TestCase):
    def test_parses_cam_style_openapi_document(self):
        document = {
            "openapi": "3.1.0",
            "info": {
                "title": "user-service",
                "version": "2.0.0",
                "description": "Imported service description",
            },
            "paths": {
                "/users/{id}": {
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "get": {
                        "operationId": "getUser",
                        "description": "Get one user",
                        "parameters": [
                            {
                                "name": "verbose",
                                "in": "query",
                                "schema": {
                                    "type": "boolean",
                                    "default": False,
                                },
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/GetUserResponse"
                                        }
                                    }
                                },
                            }
                        },
                    },
                },
                "/users": {
                    "post": {
                        "operationId": "createUser",
                        "deprecated": True,
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/CreateUserRequest"
                                    }
                                }
                            },
                        },
                        "responses": {"204": {"description": "No content"}},
                    }
                },
            },
            "components": {
                "schemas": {
                    "CreateUserRequest": {
                        "type": "object",
                        "required": ["profile"],
                        "properties": {
                            "profile": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "nickname": {"type": ["string", "null"]},
                                },
                            }
                        },
                    },
                    "GetUserResponse": {
                        "type": "object",
                        "required": ["data"],
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id"],
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                    },
                                },
                            }
                        },
                    },
                }
            },
        }

        parsed = parseOpenApiDocument(document)

        self.assertEqual(parsed["description"], "Imported service description")
        self.assertEqual(len(parsed["apis"]), 2)

        get_user = parsed["apis"][0]
        self.assertEqual(get_user["method"], "GET")
        self.assertEqual(get_user["request_params"][0]["location"], "path")
        self.assertTrue(get_user["request_params"][0]["required"])
        self.assertEqual(get_user["request_params"][1]["default_value"], "false")
        self.assertEqual(get_user["response_params"][0]["status_code"], 200)
        self.assertEqual(get_user["response_params"][0]["array_child_type"], "object")

        create_user = parsed["apis"][1]
        self.assertFalse(create_user["is_enabled"])
        profile = create_user["request_params"][0]
        self.assertEqual(profile["location"], "body")
        self.assertTrue(profile["required"])
        self.assertTrue(profile["children"][1]["nullable"])
        self.assertIn("has no body", parsed["warnings"][0])

    def test_resolves_chained_refs_and_inherits_response_status(self):
        parsed = parseOpenApiDocument(
            {
                "openapi": "3.1.0",
                "info": {"title": "test", "version": "1"},
                "paths": {
                    "/items": {
                        "get": {
                            "responses": {
                                "400": {
                                    "description": "Bad request",
                                    "content": {
                                        "application/json": {
                                            "schema": {"$ref": "#/components/schemas/ErrorAlias"}
                                        }
                                    },
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "ErrorAlias": {"$ref": "#/components/schemas/Error"},
                        "Error": {
                            "type": "object",
                            "properties": {
                                "error": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"}
                                    },
                                }
                            },
                        },
                    }
                },
            }
        )

        error = parsed["apis"][0]["response_params"][0]
        self.assertEqual(error["status_code"], 400)
        self.assertEqual(error["children"][0]["status_code"], 400)

    def test_generates_operation_id_when_missing(self):
        parsed = parseOpenApiDocument(
            {
                "openapi": "3.0.3",
                "info": {"title": "test", "version": "1"},
                "paths": {
                    "/users/{userId}": {
                        "delete": {"responses": {"204": {"description": "Deleted"}}}
                    }
                },
            }
        )

        self.assertEqual(parsed["apis"][0]["name"], "deleteUsersUserId")

    def test_rejects_unsupported_composed_schema(self):
        with self.assertRaisesRegex(OpenApiImportError, "oneOf"):
            parseOpenApiDocument(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "test", "version": "1"},
                    "paths": {
                        "/items": {
                            "post": {
                                "requestBody": {
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {"type": "integer"},
                                                ]
                                            }
                                        }
                                    }
                                },
                                "responses": {},
                            }
                        }
                    },
                }
            )

    def test_rejects_non_local_ref(self):
        with self.assertRaisesRegex(OpenApiImportError, "Only local"):
            parseOpenApiDocument(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "test", "version": "1"},
                    "paths": {
                        "/items": {
                            "get": {
                                "responses": {
                                    "200": {
                                        "$ref": "https://example.com/responses.json#/Ok"
                                    }
                                }
                            }
                        }
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
