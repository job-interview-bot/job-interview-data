import argparse
from minio_client import MinIOClient

"""
로컬 MinIO 버킷 내의 파일 삭제 (단일)

Args:
    - bucket_name : 버킷 이름
    - file_name : 버킷 내 삭제할 파일 이름
"""


def main(bucket_name: str, file_name: str):
    print(f"Bucket Name: {bucket_name}")
    print(f"File Name: {file_name}")

    client = MinIOClient()
    print("## client 접속 체크 ##")
    client.check_connect()

    client.delete_file_from_minio(bucket_name, file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process bucket name and directory path."
    )
    parser.add_argument("--bucket_name", type=str, help="Name of the bucket")
    parser.add_argument("--file_name", type=str, help="Name of the file to delete")

    args = parser.parse_args()
    main(args.bucket_name, args.file_name)
