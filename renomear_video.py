import boto3

BUCKET = "rekognition-service-face"
REGION = "us-east-2"
OLD_KEY = "2/ju-video.mp4"
NEW_KEY = "2/1CzWCpgifEY07zlBb5m34JGDWX9WaMDf0.mp4"

s3 = boto3.client("s3", region_name=REGION)

s3.copy_object(Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": OLD_KEY}, Key=NEW_KEY)
s3.delete_object(Bucket=BUCKET, Key=OLD_KEY)
print(f"OK — vídeo renomeado para {NEW_KEY}")
