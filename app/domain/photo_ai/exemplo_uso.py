"""
Exemplos de uso da API de Reconhecimento Facial.

Este arquivo serve como documentação de como usar os endpoints.
NÃO execute este arquivo diretamente - use os endpoints da API.
"""

import requests

# Configurações
BASE_URL = "http://localhost:8000"
TOKEN = "seu_token_de_autenticacao_aqui"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def exemplo_1_inicializar_colecao():
    """Exemplo 1: Inicializar a coleção do Rekognition."""
    
    url = f"{BASE_URL}/photo-ai/initialize"
    payload = {
        "collection_id": "meu_banco_de_rostos"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("Resposta:", response.json())
    
    # Resposta esperada:
    # {
    #     "success": true,
    #     "message": "Coleção 'meu_banco_de_rostos' criada com sucesso.",
    #     "collection_id": "meu_banco_de_rostos"
    # }


def exemplo_2_indexar_faces():
    """Exemplo 2: Indexar faces do bucket S3."""
    
    url = f"{BASE_URL}/photo-ai/index-faces"
    payload = {
        "s3_folder": "rostos/",
        "collection_id": "meu_banco_de_rostos"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("Resposta:", response.json())
    
    # Resposta esperada:
    # {
    #     "success": true,
    #     "total_indexed": 10,
    #     "total_skipped": 2,
    #     "total_failed": 0,
    #     "results": [
    #         {
    #             "filename": "pessoa1.jpg",
    #             "external_image_id": "pessoa1",
    #             "face_id": "abc123...",
    #             "status": "success"
    #         }
    #     ],
    #     "message": "Indexação concluída: 10 indexadas, 2 puladas, 0 falhas"
    # }


def exemplo_3_buscar_face_upload():
    """Exemplo 3: Buscar face enviando uma imagem."""
    
    url = f"{BASE_URL}/photo-ai/search-face"
    
    # Preparar o arquivo
    files = {
        'file': open('caminho/para/sua/imagem.jpg', 'rb')
    }
    
    data = {
        'threshold': 70.0,
        'max_faces': 5,
        'collection_id': 'meu_banco_de_rostos'
    }
    
    headers_multipart = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    response = requests.post(url, files=files, data=data, headers=headers_multipart)
    print("Resposta:", response.json())
    
    # Resposta esperada:
    # {
    #     "success": true,
    #     "face_detected": true,
    #     "face_confidence": 99.8,
    #     "matches": [
    #         {
    #             "name": "pessoa1",
    #             "similarity": 98.5,
    #             "face_id": "abc123..."
    #         }
    #     ],
    #     "message": "Encontradas 1 correspondência(s)"
    # }


def exemplo_4_buscar_face_s3():
    """Exemplo 4: Buscar face usando chave S3."""
    
    url = f"{BASE_URL}/photo-ai/search-face-s3"
    payload = {
        "s3_key": "rostos/teste.jpg",
        "threshold": 70.0,
        "max_faces": 5,
        "collection_id": "meu_banco_de_rostos"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("Resposta:", response.json())
    
    # Resposta similar ao exemplo 3


def exemplo_5_listar_faces():
    """Exemplo 5: Listar todas as faces indexadas."""
    
    url = f"{BASE_URL}/photo-ai/list-faces"
    payload = {
        "collection_id": "meu_banco_de_rostos",
        "max_results": 4096
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("Resposta:", response.json())
    
    # Resposta esperada:
    # {
    #     "success": true,
    #     "total_faces": 12,
    #     "faces": [
    #         {
    #             "face_id": "abc123...",
    #             "external_image_id": "pessoa1",
    #             "confidence": 99.9
    #         }
    #     ],
    #     "message": "Total de 12 face(s) indexada(s)"
    # }


def exemplo_completo_workflow():
    """
    Exemplo completo: Workflow típico de uso.
    """
    
    print("=== WORKFLOW COMPLETO ===\n")
    
    # 1. Inicializar coleção
    print("1. Inicializando coleção...")
    exemplo_1_inicializar_colecao()
    print()
    
    # 2. Indexar faces do S3
    print("2. Indexando faces do S3...")
    exemplo_2_indexar_faces()
    print()
    
    # 3. Listar faces indexadas
    print("3. Listando faces indexadas...")
    exemplo_5_listar_faces()
    print()
    
    # 4. Buscar face
    print("4. Buscando face...")
    exemplo_3_buscar_face_upload()
    print()
    
    print("=== WORKFLOW CONCLUÍDO ===")


# =============================================================================
# EXEMPLOS COM CURL (para testar no terminal)
# =============================================================================

curl_examples = """
# 1. Inicializar coleção
curl -X POST "http://localhost:8000/photo-ai/initialize" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"collection_id": "meu_banco_de_rostos"}'

# 2. Indexar faces
curl -X POST "http://localhost:8000/photo-ai/index-faces" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"s3_folder": "rostos/", "collection_id": "meu_banco_de_rostos"}'

# 3. Buscar face (upload)
curl -X POST "http://localhost:8000/photo-ai/search-face" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -F "file=@/caminho/para/imagem.jpg" \\
  -F "threshold=70.0" \\
  -F "max_faces=5" \\
  -F "collection_id=meu_banco_de_rostos"

# 4. Buscar face (S3)
curl -X POST "http://localhost:8000/photo-ai/search-face-s3" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "s3_key": "rostos/teste.jpg",
    "threshold": 70.0,
    "max_faces": 5,
    "collection_id": "meu_banco_de_rostos"
  }'

# 5. Listar faces
curl -X POST "http://localhost:8000/photo-ai/list-faces" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "collection_id": "meu_banco_de_rostos",
    "max_results": 4096
  }'
"""

if __name__ == "__main__":
    print("Este arquivo contém exemplos de uso da API.")
    print("Consulte a documentação em: http://localhost:8000/docs")
    print("\n=== EXEMPLOS COM CURL ===")
    print(curl_examples)
