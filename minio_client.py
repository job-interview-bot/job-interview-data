import os
import boto3
from pathlib import Path
from dotenv import load_dotenv

# .env 파일이 있는 경로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), "setting_object_storage/stand-alone/", ".env")

# .env 파일 로드
load_dotenv(dotenv_path)

# 환경 변수 가져오기
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

class MinIOClient:
    def __init__(self):
        # MinIO 클라이언트 생성
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ROOT_USER,
            aws_secret_access_key=MINIO_ROOT_PASSWORD
        )
    
    def check_connect(self):
        try:
            response = self.s3_client.list_buckets()
            print("Buckets:", [bucket["Name"] for bucket in response["Buckets"]])
        except Exception as e:
            print("Error connecting to MinIO:", e)

    # CSV 파일 업로드 함수
    def upload_csv_files(self, bucket_name, directory_path):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except:
            print(f"Bucket '{bucket_name}' not found. Creating now...")
            self.s3_client.create_bucket(Bucket=bucket_name)

        for file_path in Path(directory_path).glob("*.csv"):
            file_name = file_path.name
            self.s3_client.upload_file(str(file_path), bucket_name, file_name)
            print(f"Uploaded: {file_name} -> {bucket_name}/{file_name}")
    
    # 다운로드 함수
    def download_csv(self, bucket_name, file_name, download_path):
        os.makedirs(download_path, exist_ok=True)
        self.s3_client.download_file(BUCKET_NAME, file_name, f"{download_path}/{file_name}")
        print(f"Downloaded: {file_name} -> {download_path}/{file_name}")

    # 특정 파일 삭제 함수
    def delete_file_from_minio(self, bucket_name, file_name):
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_name)
            print(f"✅ 파일 삭제 완료: {file_name} from {bucket_name}")
        except Exception as e:
            print(f"❌ 파일 삭제 실패: {file_name}, 오류: {e}")