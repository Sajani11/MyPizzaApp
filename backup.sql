-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: pizzadb
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cart`
--

DROP TABLE IF EXISTS `cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cart` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `pizza_id` int NOT NULL,
  `quantity` int DEFAULT '1',
  `size` varchar(10) NOT NULL DEFAULT 'small',
  `unit_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  `toppings` text,
  `extras` text,
  `crust` varchar(50) DEFAULT 'regular',
  `cheese` varchar(50) DEFAULT 'normal',
  `toppings_hash` varchar(32) GENERATED ALWAYS AS (md5(coalesce(`toppings`,_utf8mb4''))) STORED,
  `extras_hash` varchar(32) GENERATED ALWAYS AS (md5(coalesce(`extras`,_utf8mb4''))) STORED,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_cart_item` (`user_id`,`pizza_id`,`size`,`crust`,`cheese`,`toppings_hash`,`extras_hash`),
  KEY `idx_cart_user_id` (`user_id`),
  KEY `idx_cart_pizza_id` (`pizza_id`),
  CONSTRAINT `cart_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cart_ibfk_2` FOREIGN KEY (`pizza_id`) REFERENCES `pizzas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cart`
--

LOCK TABLES `cart` WRITE;
/*!40000 ALTER TABLE `cart` DISABLE KEYS */;
INSERT INTO `cart` (`id`, `user_id`, `pizza_id`, `quantity`, `size`, `unit_price`, `toppings`, `extras`, `crust`, `cheese`) VALUES (1,2,16,1,'small',700.00,NULL,NULL,'thin','normal'),(3,6,3,1,'small',650.00,NULL,NULL,'thin','normal'),(4,6,3,2,'medium',800.00,'onions,mushrooms',NULL,'stuffed','extra'),(5,6,10,1,'small',800.00,'mushrooms',NULL,'stuffed','extra');
/*!40000 ALTER TABLE `cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `pizza_id` int NOT NULL,
  `size` varchar(10) NOT NULL,
  `quantity` int DEFAULT '1',
  `total_price` decimal(10,2) NOT NULL,
  `delivery_fee` decimal(10,2) NOT NULL DEFAULT '0.00',
  `status` varchar(50) DEFAULT 'pending',
  `payment_method` varchar(50) DEFAULT NULL,
  `contact_number` varchar(20) NOT NULL,
  `address` varchar(255) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `crust` varchar(50) DEFAULT NULL,
  `cheese` varchar(50) DEFAULT NULL,
  `toppings` text,
  `extras` varchar(100) DEFAULT NULL,
  `payment_status` varchar(50) DEFAULT 'unpaid',
  `reward` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_pizza_id` (`pizza_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_pizza_id` FOREIGN KEY (`pizza_id`) REFERENCES `pizzas` (`id`),
  CONSTRAINT `fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`pizza_id`) REFERENCES `pizzas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pizzas`
--

DROP TABLE IF EXISTS `pizzas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pizzas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `price` decimal(10,2) NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `category` varchar(50) DEFAULT NULL,
  `size` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pizzas`
--

LOCK TABLES `pizzas` WRITE;
/*!40000 ALTER TABLE `pizzas` DISABLE KEYS */;
INSERT INTO `pizzas` VALUES (1,'Cheese Pizza','Classic cheese pizza with a rich tomato base.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Mozzarella cheese, fresh basil, olive',480.00,'static/images/cheese.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(2,'Veggie Momo Pizza','A fusion of Nepali momos and pizza ? cheesy, spicy, and satisfying.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Cheese, tomato, olives, broccoli, spicy veg momo chunks',600.00,'static/images/veggie_momo.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(3,'Paneer Tikka Pizza','Spicy paneer tikka with fresh capsicum and onion for a bold taste.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Paneer tikka, capsicum, onion, tomato sauce, mozzarella',650.00,'static/images/paneer_tikka.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(4,'Corn & Mushroom Pizza','Sweet corn and fresh mushrooms layered over a tangy tomato sauce.\r\nSize: 8 inches (Normal)\r\nCategory: Vegetarian\r\nIngredients: Sweet corn, mushrooms, mozzarella, tomato sauce',500.00,'static/images/corn_mushroom.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(5,'Spicy Aloo Pizza','A Nepali twist with potato masala, green chilies, and gooey cheese.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Potato masala, green chili, mozzarella cheese, tomato base',480.00,'static/images/spicy_aloo.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(6,'Farmhouse Pizza','A wholesome veggie mix of mushrooms, capsicum, onion, and tomato.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Mushrooms, capsicum, onion, tomato, mozzarella cheese',700.00,'static/images/farmhouse.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(7,'Nepali Veg Deluxe','A deluxe treat with paneer, mushrooms, and authentic Nepali spices.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Paneer, mushrooms, onion, tomato sauce, local spices',750.00,'static/images/veg_deluxe.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(8,'Chilli Paneer Pizza','Paneer cubes tossed in a spicy Nepali-style sauce, baked with cheese.\nSize: 8 inches (Normal)\nCategory: Vegetarian\nIngredients: Paneer, chili sauce, onion, capsicum, mozzarella',720.00,'static/images/chilli_paneer.jpg','2025-06-28 05:49:40','Vegetarian','Normal (8 inches)'),(9,'Chicken Momo Pizza','Chicken Momo Pizza\nNepali-style spicy chicken momo chunks with smoky BBQ sauce.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Chicken momos, BBQ sauce, onion, mozzarella\nRs. 680.00',680.00,'static/images/chicken_momo.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(10,'Chicken Tikka Pizza','Tandoori chicken paired with onion and capsicum for an Indian twist.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Tandoori chicken, onion, capsicum, mozzarella',750.00,'static/images/chicken_tikka.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(12,'Spicy Chicken Sausage','Savory chicken sausages with chili flakes for a spicy kick.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Chicken sausages, chili flakes, mozzarella, tomato base',700.00,'static/images/chicken_sausage.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(13,'Ham & Mushroom Pizza','Tender ham slices paired with earthy mushrooms.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Ham, mushrooms, mozzarella, tomato sauce',720.00,'static/images/ham_mushroom.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(14,'Meat Lovers Pizza','The ultimate pizza for meat lovers ? loaded with ham, chicken, sausage, and extra cheese.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Ham, chicken, sausage, mozzarella cheese, tomato base',850.00,'static/images/meat_lovers.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(15,'Buff Momo Pizza','Buff momo chunks layered with onions and melted cheese.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Buff momo, onion, mozzarella, tomato sauce',650.00,'static/images/buff_momo.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(16,'Spicy Buff Pizza','Bold Nepali-style buff pizza with chili, garlic, and tomato flavors.\nSize: 8 inches (Normal)\nCategory: Non-Vegetarian\nIngredients: Buff meat, chili, garlic, tomato sauce, mozzarella',700.00,'static/images/spicy_buff.jpg','2025-06-28 05:49:40','Non-Vegetarian','Normal (8 inches)'),(21,'Hawaian Pizza','Hawaian Pizza is very popular and finger licking pizza . \r\nSize : 8 inches(Normal)\r\nCategory: Non Vegeterian\r\nIngredients: pizza dough, tomato sauce, mozzarella cheese,pineapple',699.00,'/static/images/Hawaiian_Pizza.jpg','2025-09-21 02:49:28',NULL,NULL);
/*!40000 ALTER TABLE `pizzas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `spin_rewards`
--

DROP TABLE IF EXISTS `spin_rewards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `spin_rewards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `reward` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_spin_user_id` (`user_id`),
  KEY `idx_created_at_spin` (`created_at`),
  CONSTRAINT `fk_spin_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `spin_rewards_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `spin_rewards`
--

LOCK TABLES `spin_rewards` WRITE;
/*!40000 ALTER TABLE `spin_rewards` DISABLE KEYS */;
INSERT INTO `spin_rewards` VALUES (1,6,'Extra Cheese','2025-09-21 02:27:30');
/*!40000 ALTER TABLE `spin_rewards` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(20) DEFAULT 'customer',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin Pro','adminpro12@gmail.com','scrypt:32768:8:1$y5N1mxTALQHfm37y$06a1a75b1bcf3de744cf75ad979d1ce401ceab91d8ab3543f21fe7af35184735553e431da2809e45252449ee315d6615b6056de3069db5a7f34eb2676eeb1a34','admin','2025-09-15 02:50:16'),(2,'Sejal oli','oli@gmail.com','scrypt:32768:8:1$iSkEZL40eXdGI3AF$5c2353b0aec54d30415d669252f91a36abd21717baace49466693b78b0c42518fcb1dc7cdb7c7372332f12c7e1328c913c7d79f8bbaf58733fb980d14f8b677c','customer','2025-09-20 05:24:19'),(4,'Dipendra silwal','silwalgmeil.com@1','scrypt:32768:8:1$rnqPtnL3olyOYtbz$ae5508386e93e93e4c74abf3a11a4ac996b29fa994003a1a75cc7fe9e7d3f3693cf90c3def9d5cff2ffa36de275d60f7a59c7920c6304ed25fff549efe05b7a3','customer','2025-09-21 01:58:14'),(5,'dsa sir ','dsa@sir.com','scrypt:32768:8:1$xPOxNroHfKRQrFsU$38fb5c84ec30b912bd3dd39f0d2486ba0a4e19f2b9126e0e7ea2489c6fa924860f145920d69a88387d434d498448a51ae2d29575078e85a670fa690407ef3797','customer','2025-09-21 02:10:04'),(6,'samrat piya ','samrat@gmail.com','scrypt:32768:8:1$XJd1Y33hau1qUc1t$f7bb9f9bb0110f0c81d921eedc4666cdb6dcd4d73f5672e099f0a767d2fa3cd23a1d3c655f77d5ab0008e3ad43c31b767c31472ed9cfe75fbb8e44f5c624a16e','customer','2025-09-21 02:14:42');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-21 22:43:47
