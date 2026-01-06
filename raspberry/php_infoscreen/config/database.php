<?php
class Database {
    private static $instance = null;
    private $connection;
    
    private function __construct() {
        $config = [
            'host' => $_ENV['DB_HOST'] ?? 'localhost',
            'dbname' => $_ENV['DB_NAME'],
            'username' => $_ENV['DB_USER'],
            'password' => $_ENV['DB_PASSWORD'],
        ];
        
        $dsn = "mysql:host={$config['host']};dbname={$config['dbname']};charset=utf8mb4";
        
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT => false,
        ];
        
        try {
            $this->connection = new PDO($dsn, $config['username'], $config['password'], $options);
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw new Exception("Database connection failed");
        }
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    // get porssisahko data for next hours
    // return array of data points
    public function getPorssisahkoData($timePeriod = '4h') {
        // Parse time period (e.g., '4h' -> 4 hours)
        $hours = (int) filter_var($timePeriod, FILTER_SANITIZE_NUMBER_INT);
        if ($hours <= 0) {
            $hours = 4; // default to 4 hours
        }
        
        try {
            $query = "SELECT timestamp, price 
                     FROM porssisahkonet.prices 
                     WHERE timestamp >= NOW() 
                     AND timestamp <= DATE_ADD(NOW(), INTERVAL :hours HOUR)
                     ORDER BY timestamp ASC";
            
            $stmt = $this->connection->prepare($query);
            $stmt->bindParam(':hours', $hours, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll();
            
        } catch (PDOException $e) {
            error_log("Error fetching porssisahko data: " . $e->getMessage());
            return [];
        }
    }

}
?>