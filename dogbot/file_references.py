import os

package_dir = os.path.dirname(os.path.abspath(__file__))

# These could probably be extracted to script parameters if I can move this into the apps '__main__' block or something.
config_location = os.path.join(package_dir, 'config.json')
blacklist_location = os.path.join(package_dir, 'database', 'blacklist.json')
database_location = os.path.join(package_dir, 'database', 'dog_history.db')

print("Sourcing config from: " + config_location)
print("Using the blacklist file located at: " + blacklist_location)
print("Using the database file located at: " + database_location)
