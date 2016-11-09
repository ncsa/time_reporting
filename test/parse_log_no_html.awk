BEGIN { 
    printok=1
}

/^<!DOCTYPE/ { printok=0; next }

/^<\/html/ { printok=1; next }

printok==1 { print }
