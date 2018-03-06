## Database used for college football analysis

### Getting started with MySQL on Mac OS
I wanted to learn MySQL, so the data used for this analysis was stored in a MySQL database that I called "college_football." You can download and install MySQL server for Mac OS [here](https://dev.mysql.com/downloads/mysql/5.5.html#macosx-dmg).

Open the System Preferences pane and find the MySQL icon probably at the bottom. Click on it, and then click on the "Start MySQL Server" button. You can also click on the "Stop MySQL Server" button to stop the server.

If the `mysql` command isn't found at your command prompt, try adding it to your PATH with `export PATH=$PATH:/usr/local` (e.g. add this to your .bashrc file and then `$ source ~/.bashrc`).

Next, you'll create a database as the root user (because there aren't any MySQL users other than the `root` account yet):

```bash
mysql -u root college_football
```

You just created the `college_football` MySQL database! Next, just add a user so you don't need to sign in as root every time:

```sql
GRANT ALL PRIVILEGES ON *.* TO 'local_user'@'localhost' IDENTIFIED BY 'password';
```

If you don't remember which database you're signed into, use this:

```sql
SELECT DATABASE();
```

While in a `mysql` session, if you have various `.sql` files available in your current working directory that you would like to run,
you can run it with `source [sql_file.sql]`, and the SQL in the file will execute:

```bash
mysql> source player.sql
```
