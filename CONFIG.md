### Configuration how to
 ## Operating systems
  # Debian Linux
   1. List up available locales: 
   ```bash
      # locale -a
   ```
   2. Add a locale:
   ```bash
      # sudo vim /etc/locale.gen
       (Uncomment the locale to add: 'x' remove a char)
       (Save and quit :wq)
      # locale-gen
   ```
   3. Set the locale to 'LC_ALL':
   ```bash
    # export LC_ALL=(lang_country.encoding)
   ```

