<?php
    $sV = json_decode(file_get_contents("php://input"));
    $id = $sV[0];
    $pw = $sV[1];
    
    $con = mysqli_connect("localhost", "login", "DnKPnTZH5&dDDB%v", "account");
    
    $result = mysqli_query($con, 'SELECT password, title FROM teacherAccount WHERE id = "'.$id.'"');
    $len = 0;
    $password = hash("sha256", $pw);
    $origin = "";
	
    while($ret = mysqli_fetch_assoc($result)){
        $len++;
        if($password != $ret["password"]){
            http_response_code(406);
	}
	$origin = $ret["title"];
    }
    
    if($len < 1){
        http_response_code(400);
    }
    
    $title = hash("sha256", time());
    mysqli_query($con, 'UPDATE teacherAccount SET title="'.$title.'" where id="'.$id.'"');
    rename("/var/www/html/ssch/".$origin.".html", "/var/www/html/ssch/".$title.".html");
    
    header("Content-type: text/plain, charset=UTF-8");
    echo($title);
?>
