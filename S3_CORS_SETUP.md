# Configuração de CORS para o Bucket S3

Para resolver completamente o erro `ERR_BLOCKED_BY_ORB`, você precisa configurar CORS no bucket S3.

## Passos para Configurar CORS no AWS S3

### 1. Acesse o Console da AWS
1. Vá para [AWS Console](https://console.aws.amazon.com)
2. Navegue até **S3** > Seu bucket (`n1-bucket-s3`)

### 2. Configure CORS
1. No bucket, vá para a aba **Permissions** (Permissões)
2. Role até a seção **Cross-origin resource sharing (CORS)**
3. Clique em **Edit** (Editar)
4. Cole a seguinte configuração JSON:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": [
            "ETag",
            "Content-Length",
            "Content-Type"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

**Nota:** Se você quiser restringir os origins apenas ao seu domínio, substitua `"*"` por:
```json
"AllowedOrigins": [
    "https://n1app.com.br",
    "https://www.n1app.com.br",
    "http://localhost:3000"
]
```

### 3. Configure a Política do Bucket (Opcional mas Recomendado)

Para garantir que os objetos sejam acessíveis publicamente, você também pode configurar uma política de bucket:

1. Na aba **Permissions**, vá para **Bucket policy**
2. Clique em **Edit**
3. Cole a seguinte política (substitua `n1-bucket-s3` pelo nome do seu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::n1-bucket-s3/*"
        }
    ]
}
```

### 4. Verifique o Block Public Access

1. Na aba **Permissions**, vá para **Block public access (bucket settings)**
2. Clique em **Edit**
3. **Desmarque** a opção "Block all public access" OU mantenha apenas as opções necessárias desmarcadas
4. Salve as alterações

**Atenção:** Se você desmarcar "Block all public access", certifique-se de que a política do bucket está configurada corretamente para evitar acesso não autorizado.

## Executar Script para Atualizar Arquivos Existentes

Após configurar CORS e a política do bucket, execute o script para atualizar os ACLs dos arquivos existentes:

```bash
cd back-n1
python -m scripts.fix_s3_public_access
```

Este script atualizará todos os arquivos existentes no bucket para terem ACL `public-read`.

## Verificação

Após executar o script e configurar CORS, teste acessando uma URL de imagem diretamente no navegador. Ela deve carregar sem erros.
















