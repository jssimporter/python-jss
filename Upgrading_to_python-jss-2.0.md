## Stuff you should check
- Remove any calls to `JSSObjectList.retrieve()`. The objects will fetch
  themselves when any attribute or method that needs the data is accessed.
- Consider whether to remove any `JSSObjectList.retrieve_all()` calls, as items
  will fetch themselves as they are accessed.
- Queries with the `JSS` methods named after `JSSObject`s (e.g. `JSS.Computer`)
  use optional kwargs for all "extra" query data, rather than a specific
  `subset` arg. Ensure all queries use keyword arguments rather than positional
  For example, `j.Computer('MacBook', 'general') must become
  `j.Computer('MacBook', subset='general')`.
- Some objects had helper `@property` attribute-like methods. These have all
  been removed in favor of `.` notation to access _elements_.
  
  For example, `some_computer.serial_number` just found the serial_number
  Element and returned the text. Now must do
  `some_computer.general.serial_number.text`. You can also do `print
  some_computer.general.serial_number` and it will pretty print the entire
  `Element`.
	- This change means you will always get an `Element`; if you want the text,
	  you must then append the `.text` attribute.
	  - `some_computer.general.serial_number` returns the "serial_number"
		`Element`
	  - `some_computer.general.serial_number.text` returns the computer's
		serial number as a string.
	- Specifically, the following methods have been removed in favor of dot
	  notation:
		- `Computer`/`MobileDevice`:
			- `udid()`
			- `serial_number()`
		- `ComputerGroup.criteria()`
		- `MobileDevice.wifi_mac_address()`
		- `MobileDevice.bluetooth_mac_address()`
		- `Policy`:
			- `general()`
			- `enabled()`
			- `frequency()`
			- `category()`
			- `scope()`
			- `computers()`
			- `computer_groups()`
			- `buildings()`
			- `departments()`
			- `exclusions()`
			- `excluded_computers()`
			- `excluded_computer_groups()`
			- `excluded_buildings()`
			- `excluded_departments()`
			- `self_service()`
			- `use_for_self_service()`
			- `pkg_config()`
			- `pkgs()`
			- `maintenance()`
			- `recon()`
	- Hint: Use the new `tree()` method on an instance of a class to see the
	  tag structure needed to reference any subelement.

## Stuff that is unlikely to be an issue
- Some things have been renamed; this is primarily for classes used internally,
  but if you use them for type-enforcement or checking, you will need to update
  your code:
	- Update references to `JSSObjectList` to be `QuerySet`. If instantiating
	  any directly, please note the signature has changed.
	- `JSSContainerObject` is now just `Container`
	- `JSSGroupObject` is now just `Group`
- Pickled data that references renamed or removed classes will not load. If you
  need this data, you'll need to convert it, or keep a copy of pre-2.0
  python-jss around. If this is a big deal for your use, please file an issue
  and we can work on a converter.
- `JSSObjectFactory` has been retired. Indirectly created objects using the
  `JSSObjectFactory` should be converted to use either the `JSS` constructor /
  search methods or the class itself.
- The following exception classes have been replaced with `TypeError`:
	- `JSSUnsupportedSearchMethodError`
	- `JSSUnsupportedFileType`
	- `JSSFileUploadParameterError`
	- `JSSPrefsMissingKeyError`
- `JSSPrefsMissingFileError` has been replaced with `IOError`:
- `JSSMethodNotAllowedError` is now called `MethodNotAllowedError`.
- Renamed all of the request-failure exceptions by dropping the `JSS`:
	- `JSSGetError` -> `GetError`
	- `JSSPutError` -> `PutError`
	- `JSSPostError` -> `PostError`
	- `JSStDeleteError` -> `DeleteError`
