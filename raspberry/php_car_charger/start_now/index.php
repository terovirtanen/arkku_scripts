<?php
// Front controller for /car_charger/start_now: load env, then delegate to public API

$autoload = __DIR__ . '/../vendor/autoload.php';
if (file_exists($autoload)) {
	require_once $autoload;
	if (class_exists('Dotenv\\Dotenv')) {
		Dotenv\Dotenv::createImmutable(__DIR__ . '/..')->load();
	}
}

require_once __DIR__ . '/../public/start_now.php';
?>
