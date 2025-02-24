# job-interview-data

## MinIO
- `setting_object_storage/stand-alone/` 에서 window_run.sh 실행 (포트포워딩 + 도커 실행)
- .env 파일 생성
    - 설정할 인자 목록
        - `MINIO_ENDPOINT` = `"http://localhost:9000"`
        - `MINIO_ROOT_USER` = `"admin"`
        - `MINIO_ROOT_PASSWORD` = `{8자 이상 자유 지정}`

- [업로드] MinIO 버킷 <- 로컬 데이터 (폴더 내 csv 전체)
```bash
$ python ../../minio_upload.py --bucket_name job-data --directory_path ../../sample_data/20250220
```

- MinIO 버킷 내 파일 삭제 (단일)
```bash
python ../../minio_delete.py --bucket_name job-data --file_name zighang_20250220.csv
```

- [다운로드] MinIO 버킷 -> 로컬 데이터 (단일)
```bash
python ../../minio_download.py --bucket_name job-data --file_name zighang_20250220.csv
```
