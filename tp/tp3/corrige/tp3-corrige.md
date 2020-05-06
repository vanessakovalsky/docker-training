
$ git clone https://github.com/dockersamples/linux_tweet_app 

$ docker run -d -it --name devtest -p 80:80 --mount type=bind,source="$(pwd)",target=/var/www/html  newimage


cd /var/www/html/
chown -R root:www-data .
service apache2 start

