import boto3

BUCKET = "rekognition-service-face"
REGION = "us-east-2"
COLLECTION_ID = "2"
PREFIX = "2/"

FOTOS_NOVAS = [
    "WhatsApp Image 2026-06-18 at 01.13.06 (1).jpeg",
    "WhatsApp Image 2026-06-18 at 01.13.06.jpeg",
    "WhatsApp Image 2026-06-18 at 01.13.07 (1).jpeg",
    "WhatsApp Image 2026-06-18 at 01.13.07 (2).jpeg",
    "WhatsApp Image 2026-06-18 at 01.13.07.jpeg",
]

rekognition = boto3.client("rekognition", region_name=REGION)

for nome in FOTOS_NOVAS:
    key = PREFIX + nome
    external_id = key.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    try:
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image={"S3Object": {"Bucket": BUCKET, "Name": key}},
            ExternalImageId=external_id,
            DetectionAttributes=[],
            MaxFaces=1,
            QualityFilter="AUTO",
        )
        n = len(response.get("FaceRecords", []))
        unindexed = len(response.get("UnindexedFaces", []))
        if n > 0:
            print(f"OK  {nome}")
            print(f"    {n} rosto(s) indexado(s)")
        else:
            print(f"--  {nome}")
            print(f"    nenhum rosto detectado")
            if unindexed:
                reasons = [u["Reasons"] for u in response["UnindexedFaces"]]
                print(f"    motivo: {reasons}")
    except Exception as e:
        print(f"ERR {nome}")
        print(f"    {e}")

print("\nPronto!")
