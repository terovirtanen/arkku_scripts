<?php
// Front controller: load env, then delegate to public API

// Composer autoload (dotenv and any future libs)
$autoload = __DIR__ . '/vendor/autoload.php';
if (file_exists($autoload)) {
	require_once $autoload;
	// Load .env from project root
	if (class_exists('Dotenv\\Dotenv')) {
		Dotenv\Dotenv::createImmutable(__DIR__)->load();
	}
}

require_once __DIR__ . '/public/infoscreen.php';
?>
