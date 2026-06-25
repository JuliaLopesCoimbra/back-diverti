import boto3

REGION = "us-east-2"
COLLECTION_ID = "2"
BUCKET = "rekognition-service-face"
FOTO_KEY = "2/1CzWCpgifEY07zlBb5m34JGDWX9WaMDf0.jpg"

rekognition = boto3.client("rekognition", region_name=REGION)

# Busca usando a própria foto como referência (threshold 0 = retorna tudo)
resp = rekognition.search_faces_by_image(
    CollectionId=COLLECTION_ID,
    Image={"S3Object": {"Bucket": BUCKET, "Name": FOTO_KEY}},
    MaxFaces=5,
    FaceMatchThreshold=0,
)

print("Matches mais próximos para a foto 1CzWCpgifEY07zlBb5m34JGDWX9WaMDf0.jpg:\n")
for m in resp.get("FaceMatches", []):
    print(f"  {m['Face']['ExternalImageId']} — {m['Similarity']:.1f}%")

if not resp.get("FaceMatches"):
    print("  Nenhum match encontrado")
