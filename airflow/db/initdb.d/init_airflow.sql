-- 사용자 생성
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow') THEN
        CREATE USER airflow WITH PASSWORD 'abs001101';
        RAISE NOTICE 'User airflow created.';
    END IF;
END $$;

-- 데이터베이스 생성
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow') THEN
        CREATE DATABASE airflow OWNER airflow;
        RAISE NOTICE 'Database airflow created.';
    END IF;
END $$;

-- 권한 부여 (데이터베이스 연결 없이 실행)
ALTER DATABASE airflow SET timezone TO 'Asia/Seoul';  -- 선택 사항: 타임존 설정
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
GRANT CREATE, USAGE ON SCHEMA public TO airflow;  -- 명시적 권한 부여