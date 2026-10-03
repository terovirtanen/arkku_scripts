<?php
// Front controller: load env, then delegate to public API

$autoload = __DIR__ . '/vendor/autoload.php';
if (file_exists($autoload)) {
	require_once $autoload;
	if (class_exists('Dotenv\\Dotenv')) {
		Dotenv\Dotenv::createImmutable(__DIR__)->load();
	}
}

$path = trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/');
if (basename($path) === 'start_now') {
	require_once __DIR__ . '/public/start_now.php';
} else {
	http_response_code(404);
	header('Content-Type: application/json');
	echo json_encode(['error' => 'Not found']);
}
?>
