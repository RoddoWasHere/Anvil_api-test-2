# About this API

## Introducion

This is a repository for an Anvil app which is created and modified using the Anvil app builder on the [Anvil](https://anvil.works/) website.

This is an API which allows for CRUD operations of dynamic data. The data is strongly typed. The structure of the data is specified by a dynamic schema. Both the 'data' and 'schema' is stored in the database.

### How it works:

The data structure for a particular structure type is specified by a "schema". The data is a JSON object. The schema is also specified by a JSON object.

Here's an example of a "schema" object representing a "todo list":

```JSON
{
    "name": "!string",
    "listItemIds": "!number[]",
    "desciption": "string",
}
```
The `key` here represents the name of the field and the `value` represents the data type.

the data type takes on the following form:
```
["!"]type["[]"]
```

 - `!` - specifies a required field (optional)
 - `type` - specifies the type (JavaScript type) for example "string", "number", "boolean", etc
 - `[]` - specifies that the data in this field is an array of `type` (optional)

An acceptable data object which conforms to this schema might look like this:

```JSON
{
    "name": "Main list", // string
    "listItemIds": [1, 2, 3, 4] // number[]
}
```

*Here can omit the `description` as it is not required.*__*

### Shaping data

#### Reading data

for retrieving data, a JSON POST body can optionally be included in the request. Here you can specify only the fields you wish to be returned. This can help reduce the payload.

example:
```JSON
{
    "name": "", // the value of the field here can anything here 
}
```
*The value speficied for a given field makes no different. The API only checks if the key exists.*

#### Writing data

When writing data, only the keys in the JSON POST object specified will be changed.

# API Specification

### Data

#### Read
***
<details>
<summary>
Get all by type
<code>/get_all_by_type/:schema_name</code>
</summary>

###
```
GET: /get_all_by_type/:schema_name
POST: /get_all_by_type/:schema_name
```
__Request POST body (optional):__
```JSON
{
  //...partial schema
}
```
__Response:__
```JSON
{
  //...shaped or unshaped data
}
```
</details>

***

<details>
<summary>
Get data by id
<code>/get_data/:id</code>
</summary>

###

```
GET: /get_data/:id
POST: /get_data/:id
```
__Request POST body (optional):__
```JSON
{
  //...partial schema
}
```

__Response:__
```JSON
{
  //...shaped or unshaped data
}
```
</details>

***

#### Create

***

<details>
<summary>
Create data
<code>/add_data/:schema_name</code>
</summary>

#### add
```
POST: /add_data/:schema_name
```
__Request POST body:__
```JSON
{
  //...data to add
}
```

__Response:__
```JSON
{
  //...unshaped resulting data
}
```
</details>

***

#### Update

***

<details>
<summary> 
Update data
<code>/set_data/:id</code>
</summary>

###

```
POST: /set_data/:id
```
__Request POST body:__
```JSON
{
  //...data to set (shaped)
}
```

__Response:__
```JSON
{
  //...unshaped resulting data
}
```

</details>

***

#### Delete

***

<details>
<summary> 
Delete data
<code>/delete_data/:id</code>
</summary>

###

```
POST: /delete_data/:id
```

__Response:__
```JSON
{
  //...unshaped resulting data
}
```

</details>

***