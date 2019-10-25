#!/bin/bash

FILE_SEARCH_TERM="ARM,"
TEMP_DIR="rpm2cpio_temp"
CACHE_FILE="verified_files.checklog"
FAIL_FILE="failed_files.checklog"

function check_rpm {
    isGood=1
    FILE_NAME=$1
    echo "Checking $FILE_NAME..."
    mkdir $TEMP_DIR -v
    cd $TEMP_DIR
    rpm2cpio $FILE_NAME | cpio -idm
    FILES=$(find . -type f -name '*')
    FAILED_CHECK=()
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
            FAILED_CHECK+=($FILE_INFO)
        fi
    done
    cd ..
    rm -rf $TEMP_DIR

    printf "\n\nFound problems in the following files in $FILE_NAME:"
    printf "\n"
    printf '  %s\n' "${FAILED_CHECK[@]}"
    return $isGood
}

function write_result {
    FILE_NAME=$1
    isGood=$2
    if [ $isGood == 1 ]; then
        echo "$FILE_NAME is good"
        echo "$FILE_NAME" >> $CACHE_FILE
    else
        echo "$FILE_NAME has issues"
        if grep -Fxq $FILE_NAME $FAIL_FILE; then
            echo "$FILE_NAME already exists in $FAIL_FILE"
        else
            echo "$FILE_NAME" >> $FAIL_FILE
        fi
    fi
}



touch $CACHE_FILE

echo "Clearing $FAIL_FILE..."
rm -f $FAIL_FILE
touch $FAIL_FILE

if [ "$2" != "" ]
then
    FILE_SEARCH_TERM="$2"
fi

echo "Search term(s): $FILE_SEARCH_TERM"

rm -rf $TEMP_DIR

if [ -d $1 ]; then
    echo "$1 is a directory."
    for f in $1/*.rpm
    do
        FILE_NAME="$(basename -- $f)"
        if grep -Fxq $FILE_NAME $CACHE_FILE
        then
            echo "Skipping $FILE_NAME, already verified..."
        else
            check_rpm $f
            isGood=$?
            write_result $FILE_NAME $isGood
        fi
    done
else
    if [ -f $1 ]; then
        echo "$1 is a file."
        check_rpm $1
        isGood=$?
        if [ $isGood == 1 ]; then
            exit 0
        else
            exit 1
        fi
    else
        echo "Error: $1 is not a file or directory"
        exit 1
    fi
fi

printf "\n\nThe following files have issues:\n"
echo "$(cat $FAIL_FILE)"
