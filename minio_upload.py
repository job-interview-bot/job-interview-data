import argparse
from minio_client import MinIOClient

"""
로컬 MinIO에 csv 파일들 업로드

Args:
    - bucket_name : 업로드할 버킷 이름
    - directory_path : csv가 저장되어 있는 디렉토리 경로 (경로 내에 있는 모든 csv가 업로드 대상)
"""

def main(bucket_name: str, directory_path: str):
    print(f"Bucket Name: {bucket_name}")
    print(f"Directory Path: {directory_path}")

    client = MinIOClient()
    print("## client 접속 체크 ##")
    client.check_connect()

    client.upload_csv_files(bucket_name, directory_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process bucket name and directory path.")
    parser.add_argument("--bucket_name", type=str, help="Name of the bucket")
    parser.add_argument("--directory_path", type=str, help="Path to the directory")
    
    args = parser.parse_args()
    main(args.bucket_name, args.directory_path)