<?

// UTS-www - Interface web para o UTS
// Copyright (C) 2003-2005 P. Henrique Silva <ph.silva@gmail.com>
// 
// This file is part of UTS-www.
// UTS-www is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
// 
// UTS-www is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
//

?>
<?

//function getServers() {
//  $spmservers = array();
//  $servers = array();

//  exec("python spmtable.py", $spmservers);

//  for ($i = 0; $i < count($spmservers); $i++) {
//    $tmp = split(" ", $spmservers[$i]);
//    $servers[$tmp[0]] = $tmp[1];
//  }

//  return $servers;

//}

require_once("root.php");
require_once(UTS."lib/erro.php");
require_once(UTS."config/uts.inc.php");

function createThumb($filename) {

  $fits_file = $_SESSION['bf_fullpath'] . "/" . $_GET['filename'];
  $target_file = $_SESSION['bf_fullpath'] . "/thumbs/" . basename($fits_file, ".fits") . ".jpg";
  $cmd = getcwd() . "/bin/fits2jpeg-" . UTS_PLATFORM . " -fits $fits_file -jpeg $target_file -nonLinear -quality 75";

  // choose map (linear, nonlinear)

//   if($_GET['map'] == "linear") {
//     $target_file .= "-l.jpg";
//     $cmd = getcwd() . "/bin/fits2jpeg-" . UTS_PLATFORM . " -fits $fits_file -jpeg $target_file -quality 75";
//   } else {
//     $target_file .= "-nl.jpg";
//     $cmd = getcwd() . "/bin/fits2jpeg-" . UTS_PLATFORM . " -fits $fits_file -jpeg $target_file -nonLinear -quality 75";
//   }

  if(!@file_exists($target_file)) {
    @exec($cmd, $tmp, $ret);
  }

  return "./data/" . $_SESSION['user'] . "/" . $_SESSION['inicio'] . "/thumbs/" . basename($target_file);

}

function getServers($server = null) {

    $spmout = array();
    $servers = array();

    if(!$server)
      exec(UTS_SPMTABLE_PATH . "  " . UTS_DEFAULT_SERVER, $spmout);
    else
      exec(UTS_SPMTABLE_PATH . " $server", $spmout);

    //echo "<pre>"; echo var_dump($spmout); echo "</pre>";

    if(count($spmout) < 2) {
	return FALSE;
    }

    for($i = 2; $i < count($spmout) -1; $i++) {
	$tmp = split(":", $spmout[$i]);
	$servers[trim($tmp[1])] = trim($tmp[2]);
    }

    return $servers;
}


// valida�oes
// ra  (hh:mm:ss)
// dec (+/-gg:mm:ss)
// gg 00-90
// hh 00-12
// mm 00-59
// ss 00-59

function validate_dec($dec) {

  return ereg("[0-9]{2}:[0-5][0-9]:[0-5][0-9]", $dec);

}

function dumpSession() {

  echo "<div id='debug' class='debug'>";
  echo "<pre>";
  print_r($_SESSION);
  echo "</pre>";
  echo "</div>";

}

function updateFilename($dir = "", $name = "", $index = "") {

  if($dir)
    $_SESSION['bf_dir'] = $dir;    

  if($name)
    $_SESSION['bf_name'] = $name;

  if($index)
    $_SESSION['bf_index'] = $index;

  $_SESSION['bf_fullpath'] = $_SESSION['bf_dir'] . "/" . $_SESSION['user'] . "/" . $_SESSION['inicio'];
  
  $_SESSION['bf_fullname']  = $_SESSION['bf_fullpath'] . "/" . $_SESSION['bf_name'] . "-" . (count($_SESSION['log'])+1) . "-" . strftime($_SESSION['bf_index'], time());

}

function formatSize($size) {

  # format a file size adding kb, Mb, Gb

  $res = $size / 1024.0;

  if ($res >= 1024.0) {

    $res = $res / 1024.0;

    return floor($res) . " Mb";

  } else {

    return floor($res) . " kb";
  
  }

}

function byte_format($input, $dec=0)
{
  $prefix_arr = array("", "K", "M", "G", "T");
  $value = round($input, $dec);
  while ($value>1024)
    {
      $value /= 1024;
      $i++;
    }
  $return_str = round($value, $dec).$prefix_arr[$i];
  return $return_str;
}

// Mainly based on code by: matt_DOTbevan_ATmarginsoftware_DOTcom
function mkdir_p($target) {
  // If the path already exists && is a directory, all is well.
  // If the path is not a directory, we've a problem.
  if (file_exists($target)) {
    if (!is_dir($target)) return false;
    else return true;
  }

  // Attempting to create the directory may clutter up our display.
  if (@mkdir($target, 0777))
    return @chmod($target, 0777);

}

function doLogin($nome, $user, $user_id, $root, $db) {

  if(!$root) {
	  $sql = "INSERT INTO logged VALUES('$user_id')";
	  $res =& $db->query($sql);
  }

  if(PEAR::isError($res)) {
	Header("Location: " . getError("index.php", "N&atilde;o foi poss&iacute;vel efetuar o <i>login</i>. Tente novamente."));
	exit(0);
  }

  session_start();

  $_SESSION['nome'] = $nome;
  $_SESSION['user'] = $user;
  $_SESSION['user_id'] = $user_id;
  $_SESSION['inicio'] = strftime("%Y%m%d-%H%M%Z", time());
  $_SESSION['root'] = $root;

  $_SESSION['log'] = array();
  $_SESSION['obj'] = array();
  $_SESSION['ra'] = array();
  $_SESSION['dec'] = array();
  $_SESSION['num_exp'] = array();
  $_SESSION['exp_time'] = array();
  $_SESSION['filter'] = array();
  $_SESSION['start_time'] = array();

  updateFilename(getcwd() . "/data", "imagem", "%Y%m%d%H%M%S");

  $userAreaCreated = 0;

  // create user image space
  if(!file_exists($_SESSION['bf_dir'] . "/" . $_SESSION['user']))
    mkdir_p($_SESSION['bf_dir'] . "/" . $_SESSION['user'], 0777);

  if(mkdir_p($_SESSION['bf_dir'] ."/". $_SESSION['user'] ."/". $_SESSION['inicio'], 0777)) {
    mkdir_p($_SESSION['bf_dir'] ."/". $_SESSION['user'] ."/". $_SESSION['inicio'] . "/thumbs", 0777);
    $userAreaCreated = 1;
  }	

  Header("Location: home.php?userspace=" . $userAreaCreated);

}

function userAllowed($id, $db) {

	$agora = time();

	$sql = "SELECT * FROM user_sched WHERE (user_id = $id) AND ((inicio <= $agora) AND (fim >= $agora))";
	$res =& $db->query($sql);

	if(PEAR::isError($res)) {
		return 0;
	}

	if($res->numRows()) {
		return 1;
	} else {
		return 0;
	}

}

function userUniq($id, $db) {

	$sql = "SELECT * FROM logged WHERE id = $id";
	$res =& $db->query($sql);

	if(PEAR::isError($res)) {
		return 0;
	}

	if($res->numRows()) {
		return 0;
	} else {
		return 1;
	}

}

// from MediaWiki install scripts

function replacevars( $ins, $vars ) {
	$varnames = array(
		'uts_mysql_db', 'uts_mysql_server', 'uts_mysql_user', 'uts_mysql_user_pass'
	);

	foreach ( $varnames as $var ) {
		$ins = str_replace( '{$' . $var . '}', $vars[$var], $ins );
		$ins = str_replace( '/*$' . $var . '*/`', '`' . $vars[$var], $ins );
		$ins = str_replace( '/*$' . $var . '*/', $vars[$var], $ins );
	}
	return $ins;
}

#
# Read and execute SQL commands from a file
#
function dbsource($fname, $vars, $database = false) {


	$fp = fopen( $fname, 'r' );
	if ( false === $fp ) {
		print "Could not open \"{$fname}\".\n";
		exit();
	}

	$cmd = "";
	$done = false;

	while ( ! feof( $fp ) ) {
		$line = trim( fgets( $fp, 1024 ) );
		$sl = strlen( $line ) - 1;

		if ( $sl < 0 ) { continue; }
		if ( '-' == $line{0} && '-' == $line{1} ) { continue; }

		if ( ';' == $line{$sl} ) {
			$done = true;
			$line = substr( $line, 0, $sl );
		}

		if ( '' != $cmd ) { $cmd .= ' '; }
		$cmd .= $line;

		if ( $done ) {
			$cmd = replacevars( $cmd , $vars);
			if( $database )
				$res = $database->query( $cmd );
			else
				$res = mysql_query( $cmd );

			if ( false === $res ) {
				$err = mysql_error();
				print "Query \"{$cmd}\" failed with error code \"$err\".\n";
				exit();
			}

			$cmd = '';
			$done = false;
		}
	}
	fclose( $fp );
}
?>
