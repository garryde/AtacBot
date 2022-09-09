# Demo Bot
This bot is an implement of the project [AtacBot](https://github.com/garryde/AtacBot) .

## Quick Start
Enter the bus stop number. The bus information will show in a single message. Each update will modify the same message.
![VideoToGif_GIF.GIF](https://s2.loli.net/2022/09/10/JRbqz1lAhG4xygS.gif)

## How to find the bus stop number
### 1.Find it on the bus stop.
![](https://s2.loli.net/2022/09/10/nkaUBwNv74A5QSW.png)

### 2.Use [Citymapper](https://citymapper.com/) to find it.
![](https://s2.loli.net/2022/09/10/pIUhR3oqg6VYDNO.png)

## Monitor
When you enter a valued bus stop number, the system will start a `monitor` to update your bus information.

The monitor will monitor the bus information changes for 15 minutes.

You can only have one monitor on at a time.

For example. if you enter a new bus stop number within 15 minutes of entering the last one, the system will stop the previous bus monitor and start a new one.
## Advanced command
### 1. Notify all changes
Command:
```
/notify BUS_STOP_NUMBER
```
Example:
```
/notify 70240
```

### 2. Stop Monitor
To stop a monitor if you don't want to receive the bus information anymore.

Command:
```
/stop
```

### 3. Check Monitor
Check if you have an active monitor.

Command:
```
/check
```

### 4. Set Favorites
You can bookmark frequently used bus stops.

With `/setfavorites` you can also update the NOTE of existing bus stops.

Command:
```
/setfavorites BUS_STOP_NUMBER NOTE 
```
Example:
```
/setfavorites 70240 Termini
```

### 5. Get Favorites
Get bus stops in favorites.

By clicking on the button below the message, you can quickly select a favourite bus stop and push the bus information in `/notify` mode.

Command:
```
/getfavorites
```


### 6. Delete Favorites
You can delete bus stops from your favorites

Command:
```
/delfavorites BUS_STOP_NUMBER 
```
Example:
```
/delfavorites 70240
```