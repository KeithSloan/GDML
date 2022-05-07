for i in `ls *.jpg|sed s/\.jpg//`;do convert $i.jpg -fuzz 5% -transparent white $i.png;done
