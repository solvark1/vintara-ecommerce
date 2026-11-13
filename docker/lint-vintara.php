<?php
// Run with --entrypoint php, before startup or database migrations.
if (PHP_SAPI !== 'cli') exit(1);
$count=0;
foreach(['/opt/phoenix','/var/www/html/templates/override','/var/www/html/includes/languages'] as $root) {
 foreach(new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS)) as $file) {
  if(!$file->isFile() || $file->getExtension()!=='php') continue;
  $status=0; $output=[];
  exec(escapeshellarg(PHP_BINARY).' -l '.escapeshellarg($file->getPathname()).' 2>&1',$output,$status);
  if($status!==0) { fwrite(STDERR,implode("\n",$output)."\n"); exit(1); }
  $count++;
 }
}
echo "PHP syntax verified: $count files.\n";
