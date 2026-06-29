import json
import os
import time
import urllib.request
import urllib.error


class DjangoUploadPipeline:
    BATCH_SIZE = 10

    def open_spider(self, spider):
        self.dashboard_url = spider.settings.get("DASHBOARD_URL")
        self.batch = []

        if self.dashboard_url is not None:
            if not self.dashboard_url:
                self.dashboard_url = "http://127.0.0.1:8000"
            self.dashboard_url = self.dashboard_url.rstrip("/")
            spider.logger.info("DjangoUploadPipeline enabled, target: %s", self.dashboard_url)
            self._wait_for_healthy(spider)
        else:
            spider.logger.info("DjangoUploadPipeline disabled (DASHBOARD_URL not set)")

    def _wait_for_healthy(self, spider, max_retries=10, delay=10):
        url = f"{self.dashboard_url}/health/"
        for attempt in range(1, max_retries + 1):
            try:
                spider.logger.info("Health check (attempt %d/%d)...", attempt, max_retries)
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                if data.get("status") == "healthy":
                    spider.logger.info("Backend healthy: %s", data)
                    return True
                else:
                    spider.logger.warning("Backend degraded: %s", data)
            except Exception as e:
                spider.logger.warning("Health check failed: %s", e)
            if attempt < max_retries:
                spider.logger.info("Retrying in %ds...", delay)
                time.sleep(delay)
        spider.logger.error("Backend not healthy after %d attempts, proceeding anyway", max_retries)
        return False

    def process_item(self, item, spider):
        if self.dashboard_url is None:
            return item

        self.batch.append(dict(item))

        if len(self.batch) >= self.BATCH_SIZE:
            self._flush(spider)

        return item

    def close_spider(self, spider):
        if self.dashboard_url is not None and self.batch:
            self._flush(spider)

    def _flush(self, spider, max_retries=10, delay=15):
        url = f"{self.dashboard_url}/api/ingest/bulk/"

        for attempt in range(1, max_retries + 1):
            payload = json.dumps(self.batch).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read())
                    spider.logger.info(
                        "Uploaded %d listings (%d created, %d errors)",
                        len(self.batch),
                        body.get("created", 0),
                        body.get("errors", 0),
                    )
                    self.batch = []
                    return
            except urllib.error.HTTPError as e:
                response_body = e.read().decode("utf-8", errors="replace")
                spider.logger.error(
                    "Upload failed [%d] (attempt %d/%d):\n  Response: %s\n  Payload: %s",
                    e.code, attempt, max_retries, response_body, json.dumps(self.batch, indent=2, default=str),
                )
            except urllib.error.URLError as e:
                spider.logger.error(
                    "Upload failed [URL error] (attempt %d/%d):\n  Error: %s\n  Payload: %s",
                    attempt, max_retries, e, json.dumps(self.batch, indent=2, default=str),
                )
            except Exception as e:
                spider.logger.error(
                    "Upload failed [unexpected] (attempt %d/%d):\n  Error: %s\n  Payload: %s",
                    attempt, max_retries, e, json.dumps(self.batch, indent=2, default=str),
                )

            if attempt < max_retries:
                spider.logger.info("Retrying upload in %ds...", delay)
                time.sleep(delay)

        spider.logger.error("Failed to upload %d listings after %d attempts", len(self.batch), max_retries)
        self.batch = []


class DjangoDetailUploadPipeline:
    """Pipeline for uploading detailed property data via /api/ingest/detail/."""

    def open_spider(self, spider):
        self.dashboard_url = getattr(spider, "dashboard_url", None) or spider.settings.get("DASHBOARD_URL")
        self.count = 0

        if self.dashboard_url is not None:
            if not self.dashboard_url:
                self.dashboard_url = "http://127.0.0.1:8000"
            self.dashboard_url = self.dashboard_url.rstrip("/")
            spider.logger.info("DjangoDetailUploadPipeline enabled, target: %s", self.dashboard_url)
        else:
            spider.logger.info("DjangoDetailUploadPipeline disabled (DASHBOARD_URL not set)")

    def process_item(self, item, spider):
        if self.dashboard_url is None:
            return item

        payload = dict(item)
        url = f"{self.dashboard_url}/api/ingest/detail/"

        for attempt in range(1, 6):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.count += 1
                    if self.count % 50 == 0:
                        spider.logger.info("Uploaded %d property details so far", self.count)
                    return item
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                if e.code == 404:
                    spider.logger.warning("zpid %s not in DB, skipping", payload.get("zpid"))
                    return item
                spider.logger.warning("Detail upload failed [%d] for zpid %s (attempt %d/5): %s", e.code, payload.get("zpid"), attempt, body[:200])
            except Exception as e:
                spider.logger.warning("Detail upload error for zpid %s (attempt %d/5): %s", payload.get("zpid"), attempt, e)

            if attempt < 5:
                time.sleep(3)

        spider.logger.error("Failed to upload detail for zpid %s after 5 attempts", payload.get("zpid"))
        return item

    def close_spider(self, spider):
        spider.logger.info("DjangoDetailUploadPipeline: uploaded %d property details total", self.count)
