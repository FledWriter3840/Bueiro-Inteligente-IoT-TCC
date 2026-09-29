import unittest

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.errors import register_exception_handlers


class TestApiErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/resources")
        def get_resource(resource_id: int):
            return {"id": resource_id}

        @app.get("/missing")
        def get_missing_resource():
            raise HTTPException(status_code=404, detail="Recurso não encontrado.")

        @app.get("/failure")
        def get_failure():
            raise RuntimeError("internal detail that must not leak")

        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_format_http_errors_as_problem_details(self):
        response = self.client.get("/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], "application/problem+json")
        self.assertEqual(response.json()["status"], 404)
        self.assertEqual(response.json()["detail"], "Recurso não encontrado.")

    def test_format_validation_errors_without_echoing_input(self):
        response = self.client.get("/resources", params={"resource_id": "not-an-integer"})

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["status"], 422)
        self.assertEqual(body["errors"][0]["location"], ["query", "resource_id"])
        self.assertNotIn("not-an-integer", response.text)

    def test_hide_unexpected_exception_details(self):
        with self.assertLogs("app.errors", level="ERROR"):
            response = self.client.get("/failure")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Ocorreu um erro interno.")
        self.assertNotIn("internal detail", response.text)


if __name__ == "__main__":
    unittest.main()