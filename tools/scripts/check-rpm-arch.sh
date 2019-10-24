#!/bin/bash

FILE_SEARCH_TERM="ARM,"
TEMP_DIR="rpm2cpio_temp"
CACHE_FILE="verified_files.checklog"
FAIL_FILE="failed_files.checklog"

touch $CACHE_FILE

echo "Clearing $FAIL_FILE..."
rm -f $FAIL_FILE
touch $FAIL_FILE

if [ "$2" != "" ]
then
    FILE_SEARCH_TERM="$2"
fi

echo "FILE_SEARCH_TERM: $FILE_SEARCH_TERM"

rm -rf $TEMP_DIR

for f in $1/*.rpm
do
    FILE_NAME="$(basename -- $f)"
    isGood=1
    if grep -Fxq $FILE_NAME $CACHE_FILE
    then
        echo "Skipping $FILE_NAME, already verified..."
    else
        echo "Checking $FILE_NAME..."
        mkdir $TEMP_DIR -v
        cd $TEMP_DIR
        rpm2cpio $f | cpio -idm
        FILES=$(find . -type f -name '*')
        for file in $FILES
        do
            FILE_INFO=$(file $file)
            echo "$FILE_INFO"
            # Check if it's a binary and if it was built for the correct architecture
            if [[ "$FILE_INFO" == *" ELF "* && "$FILE_INFO" != *"$FILE_SEARCH_TERM"* ]]
            then
                printf "\n\nFailed check:"
                printf "\n    RPM name: $FILE_NAME"
                printf "\n    File name: $(basename -- $file)"
                printf "\n    File info: $FILE_INFO"
                printf "\n    Search term: $FILE_SEARCH_TERM"
                printf "\n\n"
                # exit 1
                isGood=0
            fi
        done
        cd ..
        rm -rf rpm2cpio_temp
        if [ $isGood == 1 ]
        then
            echo "$FILE_NAME" >> $CACHE_FILE
        else
            if grep -Fxq $FILE_NAME $FAIL_FILE
            then
                echo "$FILE_NAME already exists in $FAIL_FILE"
            else
                echo "$FILE_NAME" >> $FAIL_FILE
            fi
        fi
    fi
done

printf "\n\nThe following files have issues:\n"
echo "$(cat $FAIL_FILE)"
