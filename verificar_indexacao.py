import boto3

REGION = "us-east-2"
COLLECTION_ID = "2"
BUSCAR = "1CzWCpgifEY07zlBb5m34JGDWX9WaMDf0"

rekognition = boto3.client("rekognition", region_name=REGION)

faces = []
next_token = None
while True:
    kwargs = {"CollectionId": COLLECTION_ID, "MaxResults": 4096}
    if next_token:
        kwargs["NextToken"] = next_token
    resp = rekognition.list_faces(**kwargs)
    faces.extend(resp.get("Faces", []))
    next_token = resp.get("NextToken")
    if not next_token:
        break

print(f"Total de faces na collection: {len(faces)}\n")

encontradas = [f for f in faces if BUSCAR in f.get("ExternalImageId", "")]
if encontradas:
    for f in encontradas:
        print(f"ENCONTRADO: {f['ExternalImageId']} | FaceId: {f['FaceId']} | Confidence: {f['Confidence']:.1f}%")
else:
    print(f"NÃO encontrado na collection: {BUSCAR}")
