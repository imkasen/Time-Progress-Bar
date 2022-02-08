# Time Progress Bar

Add a time progress bar in your README.md

# Modify your README

Add two comments to your `README.md` like this:

``` markdown
# ⏳ Life is Short

<!-- Start of Time Progress Bar -->
<!-- End of Time Progress Bar -->
```

# Extra settings

1. You can specify your time zone (`-12` ~ `+14`), the default is `UTC+0`.
    
    ``` yaml
    - uses: imkasen/time-progress-bar@master
      with:
        TIME_ZONE: +8
    ```

2. You can specify a commit message, the default is *"Update this repo's README with time progress bar"*.

    ```yaml
    - uses: imkasen/time-progress-bar@master
      with:
        COMMIT_MESSAGE: Update the README
    ```

3. You can set the block characters, the default is "░▒▓█".

    ```yaml
    - uses: imkasen/time-progress-bar@master
      with:
        BLOCKS: ⣀⣤⣶⣿
    ```

# Special Thanks

* [athul/waka-readme](https://github.com/athul/waka-readme)
