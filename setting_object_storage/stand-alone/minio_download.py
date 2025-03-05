import argparse
from minio_client import MinIOClient

"""
로컬에 MinIO 파일 다운로드 (단일)

Args:
    - bucket_name : 다운로드할 버킷 이름
    - file_name : 버킷 내의 파일 이름
    - download_path : 로컬에 다운로드 될 경로 (default="downloaded_results")
"""


def main(bucket_name: str, file_name: str, download_path: str):
    print(f"Bucket Name: {bucket_name}")
    print(f"File Name: {file_name}")
    print(f"Download_path: {download_path}")

    client = MinIOClient()
    print("## client 접속 체크 ##")
    client.check_connect()

    client.download_csv_minio2local(bucket_name, file_name, download_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process bucket name and directory path."
    )
    parser.add_argument("--bucket_name", type=str, help="Name of the bucket")
    parser.add_argument(
        "--file_name", type=str, help="Name of the file to download (e.g. filename.csv)"
    )
    parser.add_argument(
        "--download_path",
        type=str,
        default="downloaded_results",
        help="Path to the download directory",
    )

    args = parser.parse_args()
    main(args.bucket_name, args.file_name, args.download_path)
