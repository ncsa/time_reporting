BEGIN { 
    count=0
    printok=0
    outfn="test.html"
}

/DEBUG - HTML/ { print; next }

/^<!DOCTYPE/ { ++count; printok=1; outfn=count".html"; print outfn }

printok==1 { print > outfn }
#printok==1 { print }

/^<\/html/ { printok=0 }
