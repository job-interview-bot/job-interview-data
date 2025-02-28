import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from io import BytesIO
import requests
import pandas as pd
from urllib.parse import urlparse

# .env 파일이 있는 경로 직접 지정
dotenv_path = os.path.join(os.path.dirname(__file__), "setting_object_storage/stand-alone/", ".env")
load_dotenv(dotenv_path, verbose=True)


# 환경 변수 가져오기
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")


def get_file_extension(image_url):
    parsed_url = urlparse(image_url)
    file_path = parsed_url.path
    return os.path.splitext(file_path)[-1]


class MinIOClient:
    def __init__(self):
        # MinIO 클라이언트 생성
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ROOT_USER,
            aws_secret_access_key=MINIO_ROOT_PASSWORD,
        )

    # minio connect test
    def check_connect(self):
        try:
            response = self.s3_client.list_buckets()
            print("Buckets:", [bucket["Name"] for bucket in response["Buckets"]])
        except Exception as e:
            print("Error connecting to MinIO:", e)

    # csv 다운로드 함수
    def download_csv_minio2local(self, bucket_name, file_name, download_path):
        os.makedirs(download_path, exist_ok=True)
        self.s3_client.download_file(
            bucket_name, file_name, f"{download_path}/{file_name}"
        )
        print(f"Downloaded: {file_name} -> {download_path}/{file_name}")

    # img 다운로드 함수 (웹 -> minio)
    def download_img_web2minio(self, image_url):
        """주어진 URL에서 이미지를 다운로드하여 BytesIO 객체로 반환"""
        allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")

        try:
            # 올바른 확장자 추출 (쿼리 스트링 제거 후 처리)
            file_extension = get_file_extension(image_url).lower()
            if file_extension not in allowed_extensions:
                print(
                    f"❌ 지원되지 않는 이미지 형식: {image_url} (추출된 확장자: {file_extension})"
                )
                return None

            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return BytesIO(response.content)

        except requests.RequestException as e:
            print(f"❌ 이미지 다운로드 실패: {image_url}, 오류: {e}")
            return None

    # 디렉토리 내 csv 파일들 -> MinIO 업로드 함수
    def upload_csv_local2minio(self, bucket_name, directory_path):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except:
            print(f"Bucket '{bucket_name}' not found. Creating now...")
            self.s3_client.create_bucket(Bucket=bucket_name)

        for file_path in Path(directory_path).glob("*.csv"):
            # csv 파일 읽기
            df = pd.read_csv(file_path)

            for idx, row in df.iterrows():
                if row["공고본문_타입"] == "img" and isinstance(row["공고본문"], str):
                    image_url = row["공고본문"]
                    image_data = self.download_img_web2minio(image_url)

                    if image_data:
                        file_extension = (
                            get_file_extension(image_url) or ".jpg"
                        )  # 원본 확장자 유지
                        image_name = f"{row['채용사이트명']}_{row['채용사이트_공고id']}{file_extension}"
                        image_path = f"imgs/{image_name}"

                        # MinIO 업로드
                        try:
                            self.s3_client.upload_fileobj(
                                image_data, bucket_name, image_path
                            )
                            print(f"✅ 업로드 완료: {image_path}")

                            # CSV 내 이미지 경로 업데이트
                            df.at[idx, "공고본문"] = f"{bucket_name}/{image_path}"

                        except Exception as e:
                            print(f"❌ 이미지 업로드 실패: {image_name}, 오류: {e}")

            df.to_csv(file_path, index=False)
            print(f"✅ CSV 업데이트 완료 (로컬 저장): {file_path}")

            try:
                self.s3_client.upload_file(str(file_path), bucket_name, file_path.name)
                print(
                    f"✅ 업데이트된 CSV MinIO 업로드 완료: {file_path.name} -> {bucket_name}/{file_path.name}"
                )

            except Exception as e:
                print(f"❌ 업데이트된 CSV 업로드 실패, 오류: {e}")

    # 특정 파일 삭제 함수
    def delete_file_from_minio(self, bucket_name, file_name):
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file_name)
            print(f"✅ 파일 삭제 완료: {file_name} from {bucket_name}")
        except Exception as e:
            print(f"❌ 파일 삭제 실패: {file_name}, 오류: {e}")
