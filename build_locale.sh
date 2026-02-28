fd -t f -e py src | xargs rg -l "_\(|N\(_" >po/POTFILES
fd -t f '.*\.xml$|.*\.in$' data >>po/POTFILES
xgettext -o po/zeroneai.pot $(cat po/POTFILES)
cd po
for file in $(fd -e po); do
	msgmerge -U "$file" zeroneai.pot
done
rm -f *~
