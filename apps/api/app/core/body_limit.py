from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    """Bound request memory before JSON or multipart parsing, including chunked uploads."""
    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks, total = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data = message.get("body", b"")
            total += len(data)
            if total > self.max_bytes:
                return await JSONResponse({"detail": "Request body is too large"}, status_code=413)(scope, receive, send)
            chunks.append(data)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()
        await self.app(scope, replay, send)
