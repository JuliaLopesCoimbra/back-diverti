import boto3
import os

BUCKET = "rekognition-service-face"
REGION = "us-east-2"
COLLECTION_ID = "2"

FOTO = "2/1CzWCpgifEY07zlBb5m34JGDWX9WaMDf0.jpg"

rekognition = boto3.client("rekognition", region_name=REGION)

external_id = os.path.splitext(os.path.basename(FOTO))[0]  # sem extensão, sem pasta

resp = rekognition.index_faces(
    CollectionId=COLLECTION_ID,
    Image={"S3Object": {"Bucket": BUCKET, "Name": FOTO}},
    ExternalImageId=external_id,
    DetectionAttributes=[],
    MaxFaces=1,
    QualityFilter="AUTO",
)

n = len(resp.get("FaceRecords", []))
if n > 0:
    print(f"OK — rosto indexado com ExternalImageId='{external_id}'")
else:
    unindexed = resp.get("UnindexedFaces", [])
    reasons = [u["Reasons"] for u in unindexed] if unindexed else []
    print(f"Nenhum rosto detectado. Motivo: {reasons}")
