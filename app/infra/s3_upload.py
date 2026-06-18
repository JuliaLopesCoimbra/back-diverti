import boto3
from botocore.exceptions import NoCredentialsError
from app.config.settings import settings
import uuid
import re
import unicodedata
from typing import List
from fastapi import HTTPException

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION
)

# Constantes de tamanho
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Converter MB para bytes
MAX_TOTAL_SIZE_BYTES = settings.MAX_TOTAL_SIZE_MB * 1024 * 1024

def _get_file_size(file_obj) -> int:
    """
    Obtém o tamanho do arquivo em bytes.
    """
    # Salvar posição atual
    current_position = file_obj.tell()
    
    # Ir para o final do arquivo para obter o tamanho
    file_obj.seek(0, 2)  # 2 = SEEK_END
    file_size = file_obj.tell()
    
    # Voltar para a posição original
    file_obj.seek(current_position)
    
    return file_size

def _sanitize_filename(filename: str) -> str:
    """Remove acentos, espaços e chars especiais do nome do arquivo para gerar S3 key segura."""
    # Normaliza acentos → ASCII equivalente
    normalized = unicodedata.normalize("NFKD", filename)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    # Substitui qualquer char que não seja letra, dígito, ponto ou hífen por _
    safe = re.sub(r"[^\w.\-]", "_", ascii_name)
    return safe or "file"


def _validate_file_size(file_obj, filename: str) -> None:
    """
    Valida o tamanho do arquivo antes do upload.
    Levanta HTTPException se o arquivo for muito grande.
    """
    file_size = _get_file_size(file_obj)
    
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        max_mb = settings.MAX_FILE_SIZE_MB
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo '{filename}' muito grande ({size_mb:.2f} MB). Tamanho máximo permitido: {max_mb} MB."
        )
    
    # Resetar ponteiro para o início
    file_obj.seek(0)

def upload_image_to_s3(image_file, folder: str):
    """
    folder: ex -> 'news_photos' | 'event_photos'
    """
    # Validar tamanho do arquivo antes do upload
    _validate_file_size(image_file.file, image_file.filename)

    safe_name = _sanitize_filename(image_file.filename)
    file_name = f"{folder}/{uuid.uuid4()}_{safe_name}"

    try:
        s3_client.upload_fileobj(
            image_file.file,
            settings.AWS_BUCKET,
            file_name,
            ExtraArgs={"ContentType": image_file.content_type}
        )

        return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{file_name}"

    except NoCredentialsError:
        raise Exception("Credenciais da AWS não encontradas.")
    except HTTPException:
        # Re-raise HTTPException (erro de validação de tamanho)
        raise
    except Exception as e:
        raise Exception(f"Erro ao fazer upload: {str(e)}")

def upload_news_images_to_s3(image_files: List, post_id: int, folder: str = "news_photos"):
    """
    Faz upload de múltiplas imagens para uma news específica.
    Estrutura: {folder}/{post_id}/{uuid}_{filename}
    
    Args:
        image_files: Lista de UploadFile
        post_id: ID do post de notícia
        folder: Pasta base (padrão: 'news_photos')
    
    Returns:
        Lista de URLs das imagens em ordem
    """
    # Validar tamanho total de todos os arquivos
    total_size = 0
    for image_file in image_files:
        image_file.file.seek(0)
        file_size = _get_file_size(image_file.file)
        total_size += file_size
        
        # Validar tamanho individual
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            max_mb = settings.MAX_FILE_SIZE_MB
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo '{image_file.filename}' muito grande ({size_mb:.2f} MB). Tamanho máximo permitido: {max_mb} MB."
            )
    
    # Validar tamanho total
    if total_size > MAX_TOTAL_SIZE_BYTES:
        total_mb = total_size / (1024 * 1024)
        max_total_mb = settings.MAX_TOTAL_SIZE_MB
        raise HTTPException(
            status_code=413,
            detail=f"Tamanho total dos arquivos ({total_mb:.2f} MB) excede o limite permitido ({max_total_mb} MB)."
        )
    
    image_urls = []
    
    for index, image_file in enumerate(image_files):
        # Resetar o ponteiro do arquivo para garantir que está no início
        image_file.file.seek(0)
        
        # Nome do arquivo: {folder}/{post_id}/{uuid}_{filename}
        file_name = f"{folder}/{post_id}/{uuid.uuid4()}_{image_file.filename}"

        try:
            s3_client.upload_fileobj(
                image_file.file,
                settings.AWS_BUCKET,
                file_name,
                ExtraArgs={"ContentType": image_file.content_type}
            )

            url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{file_name}"
            image_urls.append(url)
            
        except NoCredentialsError:
            raise Exception("Credenciais da AWS não encontradas.")
        except HTTPException:
            # Re-raise HTTPException (erro de validação)
            raise
        except Exception as e:
            raise Exception(f"Erro ao fazer upload da imagem {index + 1}: {str(e)}")
    
    return image_urls

def upload_product_images_to_s3(image_files: List, product_id: int, folder: str = "product_photos"):
    """
    Faz upload de múltiplas imagens para um produto específico.
    Estrutura: {folder}/{product_id}/{uuid}_{filename}
    
    Args:
        image_files: Lista de UploadFile
        product_id: ID do produto
        folder: Pasta base (padrão: 'product_photos')
    
    Returns:
        Lista de URLs das imagens em ordem
    """
    # Validar tamanho total de todos os arquivos
    total_size = 0
    for image_file in image_files:
        image_file.file.seek(0)
        file_size = _get_file_size(image_file.file)
        total_size += file_size
        
        # Validar tamanho individual
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            max_mb = settings.MAX_FILE_SIZE_MB
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo '{image_file.filename}' muito grande ({size_mb:.2f} MB). Tamanho máximo permitido: {max_mb} MB."
            )
    
    # Validar tamanho total
    if total_size > MAX_TOTAL_SIZE_BYTES:
        total_mb = total_size / (1024 * 1024)
        max_total_mb = settings.MAX_TOTAL_SIZE_MB
        raise HTTPException(
            status_code=413,
            detail=f"Tamanho total dos arquivos ({total_mb:.2f} MB) excede o limite permitido ({max_total_mb} MB)."
        )
    
    image_urls = []
    
    for index, image_file in enumerate(image_files):
        # Resetar o ponteiro do arquivo para garantir que está no início
        image_file.file.seek(0)
        
        # Nome do arquivo: {folder}/{product_id}/{uuid}_{filename}
        file_name = f"{folder}/{product_id}/{uuid.uuid4()}_{image_file.filename}"

        try:
            s3_client.upload_fileobj(
                image_file.file,
                settings.AWS_BUCKET,
                file_name,
                ExtraArgs={"ContentType": image_file.content_type}
            )

            url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{file_name}"
            image_urls.append(url)
            
        except NoCredentialsError:
            raise Exception("Credenciais da AWS não encontradas.")
        except HTTPException:
            # Re-raise HTTPException (erro de validação)
            raise
        except Exception as e:
            raise Exception(f"Erro ao fazer upload da imagem {index + 1}: {str(e)}")
    
    return image_urls

def upload_event_map_images_to_s3(image_files: List, event_id: int, folder: str = "map_images"):
    """
    Faz upload de múltiplas imagens do mapa para um evento específico.
    Estrutura: {folder}/{event_id}/{uuid}_{filename}
    
    Args:
        image_files: Lista de UploadFile
        event_id: ID do evento
        folder: Pasta base (padrão: 'map_images')
    
    Returns:
        Lista de URLs das imagens em ordem
    """
    # Validar tamanho total de todos os arquivos
    total_size = 0
    for image_file in image_files:
        image_file.file.seek(0)
        file_size = _get_file_size(image_file.file)
        total_size += file_size
        
        # Validar tamanho individual
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            max_mb = settings.MAX_FILE_SIZE_MB
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo '{image_file.filename}' muito grande ({size_mb:.2f} MB). Tamanho máximo permitido: {max_mb} MB."
            )
    
    # Validar tamanho total
    if total_size > MAX_TOTAL_SIZE_BYTES:
        total_mb = total_size / (1024 * 1024)
        max_total_mb = settings.MAX_TOTAL_SIZE_MB
        raise HTTPException(
            status_code=413,
            detail=f"Tamanho total dos arquivos ({total_mb:.2f} MB) excede o limite permitido ({max_total_mb} MB)."
        )
    
    image_urls = []
    
    for index, image_file in enumerate(image_files):
        # Resetar o ponteiro do arquivo para garantir que está no início
        image_file.file.seek(0)
        
        # Nome do arquivo: {folder}/{event_id}/{uuid}_{filename}
        file_name = f"{folder}/{event_id}/{uuid.uuid4()}_{image_file.filename}"

        try:
            s3_client.upload_fileobj(
                image_file.file,
                settings.AWS_BUCKET,
                file_name,
                ExtraArgs={"ContentType": image_file.content_type}
            )

            url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{file_name}"
            image_urls.append(url)
            
        except NoCredentialsError:
            raise Exception("Credenciais da AWS não encontradas.")
        except HTTPException:
            # Re-raise HTTPException (erro de validação)
            raise
        except Exception as e:
            raise Exception(f"Erro ao fazer upload da imagem {index + 1}: {str(e)}")
    
    return image_urls
