# TP6: Build your own register

This TP allows us to install our own private register within a docker to manage our images, but also to secure it by adding a certifat SSL and a basic authentication mechanism 

## Step 1 - Install our private register
- Create a docker-compose.yml file
- Declare a service for our register that relies on the image: Registry: 2
- Add in environmental variable to our service:
```
REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY: /data
```
- Also add a volume, get into the container on /data (or any other path use in the environment variable)
-The private register must then be accessible on URL-de-Votre-Host: 5000 (if you are on the Labs Remember to open Port 5000)

## Step 2 - Secure our private register

-To start, create SSL certificates (these are self-generated they generate a warning message in the browser, you can also use Let's Encrypt to obtain certificates recognized by browsers).Handle to do on the host machine)

* On Linux host
```
mkdir certs
openssl req \
    -newkey rsa:4096 -nodes -sha256 -keyout certs/localhost.key \
    -x509 -days 365 -out certs/localhost.crt

```
* On Windoows host, to install openssl : https://slproweb.com/products/Win32OpenSSL.html 



- Now add the following options to the Docker Composed service (these are the options used with a Docker Run for you to transform them into a syntax for Docker-Concomose)
 ```
    -v "$(pwd)"/certs:/certs \         
   -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/localhost.crt \
   -e REGISTRY_HTTP_TLS_KEY=/certs/localhost.key \
   -p 443:443 
```
- Do not forget to add the volume to the backrest containing the certificates
- Relaunch the application
```
docker-compose stop
docker-compose down
docker-compose up
```
- It is now possible to access the API securely to list the images (once the warning message of the browser has accepted)
Url-de-Votre-Hote/V2/_Catalog

## Step 3 - Restress access to the private register

- It is necessary to add authentication, to this use HTPASSWD (creation of a folder then generation from our container of the HTPASSWD file)
```
 mkdir auth
 docker run \
  --entrypoint htpasswd \
  httpd:2 -Bbn testuser testpassword > auth/htpasswd
```
- The file being generated, it remains to use it in our Docker-Complete to restrict access
- Add to the Docker service composes the following information (still coming from the Docker Run command therefore to adapt)
```
-v "$(pwd)"/data:/var/lib/registry \
    -v "$(pwd)"/auth:/auth \
    -e "REGISTRY_AUTH=htpasswd" \
    -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
    -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
```
- Remember to restart the Docker's application composed
- The register is now secure

## Step 4 - Place your images in your private register
- Start by connecting
```
docker login URL-DE-VOTRE-HOST:5000
```
- Then once the username and the password have seized, it is possible to push its own images (after having commitéw and tagged):
```
docker commit <containerID> newimage
docker tag newimage URL-DE-VOTRE-HOST:5000/newimage
docker push URL-DE-VOTRE-HOST:5000/newimage:latest
```
- the private register is ready to be used
