# arkku_scripts
My scripts run on arkku.net


To run the PHPUnit tests on Ubuntu, follow these steps:

1. Install PHP and Composer: If you don't have PHP and Composer installed, you can install them using the following commands:
sudo apt update
sudo apt install php php-cli php-xml unzip
curl -sS https://getcomposer.org/installer | php
sudo mv composer.phar /usr/local/bin/composer


2. Install PHPUnit: Use Composer to install PHPUnit. Navigate to your project directory and run:
composer require --dev phpunit/phpunit

3. Ensure Directory Structure: Make sure your directory structure looks something like this:
project-root/
├── composer.json
├── composer.lock
├── vendor/
│   └── bin/
│       └── phpunit
├── root/
│   └── SolarPower.php
└── tests/
    └── SolarFieldPowerTest.php

4.Run the Tests: Navigate to your project directory and run the PHPUnit tests using the following command:
./vendor/bin/phpunit tests/SolarFieldPowerTest.php

This command will execute the tests defined in the SolarFieldPowerTest.php file.

Example composer.json
If you don't have a composer.json file, you can create one with the following content:
{
    "require-dev": {
        "phpunit/phpunit": "^9.5"
    }
}

Then run composer install to install PHPUnit.

Example Output
When you run the tests, you should see output similar to this:
PHPUnit 9.5.10 by Sebastian Bergmann and contributors.

....                                                                4 / 4 (100%)

Time: 00:00.123, Memory: 6.00 MB

OK (4 tests, 8 assertions)

This indicates that all tests have passed successfully.

By following these steps, you should be able to run your PHPUnit tests on Ubuntu and verify the functionality of your SolarFieldPower class.

# show chart.html with data json
python3 -m http.server 8000
http://localhost:8000/chart.html