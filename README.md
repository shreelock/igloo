igloo
===

Attempt at managing Libre Notifications in a better way, 
since the native app does not provide the functionality.

Currently works with Telegram Notifications.

References :
1. https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/
2. https://github.com/DiaKEM/libre-link-up-api-client
3. https://gist.github.com/khskekec/6c13ba01b10d3018d816706a32ae8ab2


Set up a service
```commandline
sudo vim /etc/systemd/system/igloo_populator.service
```

```
[Unit]
Description=igloo populator service

[Service]
ExecStart=/usr/bin/python3 -u /home/dietpi/projects/igloo/igloobot/run.py --populator
WorkingDirectory=/home/dietpi/projects/igloo/
StandardOutput=journal
StandardError=journal
Restart=always
User=dietpi

[Install]
WantedBy=multi-user.target
sudo systemctl daemon-reload
```

```commandline
sudo systemctl daemon-reload
sudo systemctl restart igloo_populator.service

sudo journalctl -u igloo_populator.service -f
```
