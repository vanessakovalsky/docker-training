# TP6: Build your own register

This TP allows us to install our own private register within a docker to manage our images, but also to secure it by adding a certifat SSL and a basic authentication mechanism 

## Step 1 - Install our private register
- Create a docker-compose.yml file
- Declare a service for our register that relies on the image: Registry: 2
- Add in environmental variable to our service:
```
Regisry_storage_filesystem_rootdirectory: /data
```
- Also add a volume, get into the container on /data (or any other path use in the environment variable)
-The private register must then be accessible on URL-de-Votre-Host: 5000 (if you are on the Labs Remember to open Port 5000)

## Step 2 - Secure our private register

-To start, create SSL certificates (these are self-generated they generate a warning message in the browser, you can also use Let's Encrypt to obtain certificates recognized by browsers).Handle to do on the host machine)
```
MKDIR CERTS
OpenSSL REQ \
    -Newkey RSA: 4096 -Nodes -Sha256 -Keyout Certs/Localhost.key \
    -x509 -Days 365 --ou Certs/Localhost.crt
```
- Now add the following options to the Docker Composed service (these are the options used with a Docker Run for you to transform them into a syntax for Docker-Concomose)
 ```
     -v "$ (pwd)"/Certs:/Certs \
    -e regisry_http_tls_certificate =/Certs/Localhost.crt \
    -E regisry_http_tls_key =/Certs/Localhost.key \
    -p 443: 443 \
```
- Do not forget to add the volume to the backrest containing the certificates
- Relaunch the application
```
Docker-compose Stop
Docker-compose Down
Docker-compose up
```
- It is now possible to access the API securely to list the images (once the warning message of the browser has accepted)
Url-de-Votre-Hote/V2/_Catalog

## Step 3 - Restress access to the private register

- It is necessary to add authentication, to this use HTPASSWD (creation of a folder then generation from our container of the HTPASSWD file)
```
 MKDIR AUTH
 Docker Run \
  -entrypoint htpasswd \
  HTTPD: 2 -Bbn Testuser Testpassword> Auth/htpasswd
```
- The file being generated, it remains to use it in our Docker-Complete to restrict access
- Add to the Docker service composes the following information (still coming from the Docker Run command therefore to adapt)
```
-v "$ (pwd)"/data:/var/lib/registry \
    -v "$ (pwd)"/author:/author \
    -e "registry_auth = htpasswd" \
    -e "registry_auth_htpasswd_realm = registry realm" \
    -e regisry_auth_htpasswd_path =/author/htpasswd \
`` `
- Remember to restart the Docker's application composed
- The register is now secure

## Step 4 - Place your images in your private register
- Start by connecting
`` `
Docker Login Url-de-Votre-Host: 5000

`` `
- Then once the username and the password have seized, it is possible to push its own images (after having commitéw and tagged):
`` `
Docker Commit <containerid> Newimage
Docker Tag Newimage Url-de-Votre-Host: 5000/Newimage
Docker Push Url-de-Votre-Host: 5000/Newimage: Latest
`` `
- the private register is ready to be used
