import alibabacloud_oss_v2 as oss
import uuid
from pathlib import Path
from datetime import datetime

class OSSService:
    def __init__(self, config: dict):
        self.config = config

    def gerenate_presigned_url(self, key: str) -> str | None:
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
        config = oss.config.load_default()
        config.credentials_provider = credentials_provider
        config.region = self.config["region"]
        client = oss.Client(config)

        # 生成下载链接
        pre_result = client.presign(
            oss.GetObjectRequest(
                bucket=self.config["bucket_name"],
                key=key
            )
        )
        return pre_result.url

    def upload_file(self, file_path: str) -> str | None:
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
        config = oss.config.load_default()
        config.credentials_provider = credentials_provider
        config.region = self.config["region"]

        path = Path(file_path)
        
        file_name = datetime.now().strftime(f"%Y-%m-%d:{uuid.uuid4()}{path.suffix}")
        client = oss.Client(config)
        with open(file_path, "rb") as f:
            result = client.put_object(
                oss.PutObjectRequest(
                    bucket=self.config["bucket_name"],
                    key=file_name,
                    body=f
                )
            )
            if result.status != "OK":
                return None
        
        return file_name
