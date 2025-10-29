igloo
===

Attempt at managing Libre Notifications in a better way, 
since the native app does not provide the functionality.

Currently works with Telegram Notifications.

References :
1. https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/
2. https://github.com/DiaKEM/libre-link-up-api-client
3. https://gist.github.com/khskekec/6c13ba01b10d3018d816706a32ae8ab2

Other apt installs
- sudo apt-get install libopenjpeg-dev -y
- sudo apt-get install libopenjp2-7


Set up a service
```commandline
sudo vim /etc/systemd/system/igloo_populator.service
```

```
[Unit]
Description=igloo populator service

[Service]
ExecStart=/usr/bin/python3 -u /home/ubuntu/igloo/igloobot/run.py --populator
WorkingDirectory=/home/ubuntu/igloo/
StandardOutput=journal
StandardError=journal
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```


```commandline
sudo vim /etc/systemd/system/igloo_notifier.service
```

```
[Unit]
Description=igloo notifier service

[Service]
ExecStart=/usr/bin/python3 -u /home/ubuntu/igloo/igloobot/run.py --notifier
WorkingDirectory=/home/ubuntu/igloo/
StandardOutput=journal
StandardError=journal
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```commandline
sudo vim /etc/systemd/system/igloo_jarvis.service
```

```
[Unit]
Description=igloo jarvis service

[Service]
ExecStart=/usr/bin/python3 -u /home/ubuntu/igloo/igloobot/run.py --jarvis
WorkingDirectory=/home/ubuntu/igloo/
StandardOutput=journal
StandardError=journal
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```commandline
sudo systemctl daemon-reload
sudo systemctl restart igloo_populator.service
sudo systemctl restart igloo_notifier.service
sudo systemctl restart igloo_jarvis.service

sudo journalctl -u igloo_populator.service -f
sudo journalctl -u igloo_notifier.service -f
sudo journalctl -u igloo_jarvis.service -f

```

```commandline
sudo systemctl restart igloo_populator.service && sudo journalctl -u igloo_populator.service -f
sudo systemctl restart igloo_notifier.service && sudo journalctl -u igloo_notifier.service -f
sudo systemctl restart igloo_jarvis.service && sudo journalctl -u igloo_jarvis.service -f

```
