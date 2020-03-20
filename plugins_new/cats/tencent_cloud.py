import datetime
import ujson
import hashlib
import hmac
from io import StringIO
import ujson
import time


def hmac_sha256(key: bytes, value: bytes) -> bytes:
    return hmac.new(key, value, digestmod="SHA256").digest()


def make_header(payload: str, timestamp, secret_id, secret_key) -> dict:
    date = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    request = StringIO()
    request.write('POST\n')
    request.write("/\n")
    request.write("\n")
    request.write(
        "content-type:application/json\nhost:tiia.tencentcloudapi.com\n\n")
    request.write("content-type;host\n")
    request.write(hashlib.sha256(payload.encode()).hexdigest())
    # print(request.getvalue())
    # print("-----------------------")
    scope = date + "/tiia/tc3_request"
    string_to_sign = (
        "TC3-HMAC-SHA256\n" +
        f"{timestamp}\n" +
        scope+"\n" +
        hashlib.sha256(request.getvalue().encode()).hexdigest()
    )
    # print(string_to_sign)
    # print("-----------------------")
    secret_date = hmac_sha256(f"TC3{secret_key}".encode(), date.encode())
    secret_service = hmac_sha256(secret_date, b"tiia")
    secret_signing = hmac_sha256(secret_service, b"tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode(), "SHA256").hexdigest()
    # print(signature)
    # print("-----------------------")
    authorization = (
        f"TC3-HMAC-SHA256 Credential={secret_id}/{scope}, SignedHeaders=content-type;host, Signature={signature}"
    )
    # print(authorization)
    # print("-----------------------")
    return {
        "X-TC-Action": "DetectLabel",
        "X-TC-Version": "2019-05-29",
        "X-TC-Region": "ap-beijing",
        "X-TC-Timestamp": str(timestamp),
        "Host": "tiia.tencentcloudapi.com",
        "Content-Type": "application/json",
        "Authorization": authorization
    }
